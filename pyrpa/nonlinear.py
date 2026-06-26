'''

'''

import numpy as np

class postik(object):

    def __init__(self, probabilities, cutoffs, zmin, zmax, lttype=1, ltpar=1., uttype=1, utpar=1., discretization=1000,
                 localize=False, panel_xyz=None, smu_xyz=None, smu_grades=None,
                 panel_origin=None, panel_bsize=None, panel_numblocks=None):

        '''
        Multiple Indicator Kriging (MIK) class.

        The class initiatilization does not include the support correction parameter, order relations correction
        specification or confidence interval parameter. This is specified in the class function postik.process()

        This postik class is roughly based on the postik.f90 code.
        The class allows for localization of equally sized sub-block smus within the parent block panel. The panel
        is not required to be filled with blocks. The number of smus inside each panel is counted and the conditional
        distribution is divided among the number of smus counted only.
        
        Parameters
        ----------

        probabilities: 2D numpy array containing floats with shape (len(probabilities), number of cutoffs)
        cutoffs: 1D numpy array
        zmin: float
        Minimum extrapolation limit
        zmax: float
        Maximum extrapolation limit
        lttype: integer
        Lower tail interpolation type (1=linear, 3=power, 4=hyperbolic)
        ltpar: float
        Lower tail parameter; To be used with the power model. <1 is positively skewed, 1 is straight line, >1
        negatively skewed
        uttype: integer
        upper tail interpolation type (1=linear, 3=power, 4=hyperbolic)
        upar: float
        Upper tail parameter; For the power and hyperbolic models. Power parameter as per lower tail parameter. For the
        hyperbolic model, the parameter lies on interval (0,1).
        discretization: integer
        Number of discretization points/interpolated z-values along the cdf. Default = 100 but 1000 points advised,
        minimal additional computation time.
        localize: Boolean, default = False
        panel_xyz: 2D array of floats with shape (len(panel_xyz), 3)
        Required if localize=True
        smu_xyz: 2D array of floats with shape (len(smu_xyz), 3)
        Required if localize=True
        smu_grades: 1D array of floats with length=len(smu_grades)
        panel_origin: list or 1D array of floats with length=3
        Optional but used if localize=True. If no setup given the origin will be calculated from the blocks.
        panel_bsize: list or 1D array of floats with length=3
        Optional but used if localize=True. If no setup given the block size will be calculated from the blocks.
        panel_numblocks: list or 1D array of integers with length=3
        Optional but used if localize=True. If no setup given the number of blocks will be calculated from the blocks.

        Notes
        --------

        The block model should be sorted by the 'Datamine' IJK for localization to work correctly

        '''

        self.probabilities = 1.0 - probabilities
        self.cutoffs = cutoffs
        self.zmin = zmin
        self.zmax = zmax
        self.lttype = lttype
        self.ltpar = ltpar
        self.uttype = uttype
        self.utpar = utpar
        self.discretization = discretization
        self.localize = localize


        if self.localize:
            self.panel_xyz = panel_xyz
            self.smu_xyz = smu_xyz
            self.smu_grades = smu_grades
            if panel_origin is None or panel_bsize is None or panel_numblocks is None:
                print("Model setup not specified, estimating model setup...")
                self.panel_origin, self.panel_bsize, self.panel_numblocks = _estimate_block_definition(self.panel_xyz)
                print("Origin =", self.panel_origin, "Block Size =",self.panel_bsize, "Number of Blocks =",self.panel_numblocks)
            else:
                self.panel_origin = panel_origin
                self.panel_bsize = panel_bsize
                self.panel_numblocks = panel_numblocks

    def process(self, varadj=0.5, adjtype=1, report_cutoffs=None, or_corr=True, ci=90.):

        '''

        Post-process the mik probabilities:

        Options included:
        1. Order relations correction
        2. Support correction (ILC and Affine)
        3. Localization
        4. Custom reporting cut-offs
        5. Custom confidence interval


        varadj: float
        Variance adjustment factor (1 - standardised gammabar +- information effect)
        adjtype: integer
        Support correction model to use: 1=Affine, 2=Indirect Lognormal Correction
        report_cutoffs: 1D array or list
        Optional. The reporting cut-offs can be different than the cut-offs used during estimation
        or_corr: Boolean
        Perform upwards and downwards order relations correction
        CI: float
        Confidence interval to report. Default = 90.

        Returns
        -------

        self.prabs: 2D numpy array of floats with shape (len(self.prabs), 3)
        probability above report_cutoffs
        self.grabs: 2D numpy array of floats with shape (len(self.grabs), 3)
        grade above report_cutoffs
        self.etype: 1D numpy array of floats with length = len(self.probabilities)
        Average grade of the panel
        self.cvar: 1D numpy array of floats with length = len(self.probabilities)
        Conditionsl variance/panel variance
        self.CI: 1D numpy array of floats with length = len(self.probabilities)
        Confidence interval based on CI parameter
        self.localized: 1D numpy array of floats with length = len(self.smu_grades)

        Notes
        -----

        '''

        if report_cutoffs is None:
            report_cutoffs = self.cutoffs

        numcuts = len(report_cutoffs)
        lenprabs = len(self.probabilities[:, 0])
        self.prabs = np.zeros((lenprabs, numcuts))
        self.grabs = np.zeros((lenprabs, numcuts))
        self.etype = np.zeros(lenprabs)
        self.cvar = np.zeros(lenprabs)
        self.ci = np.zeros(lenprabs)

        if self.localize:

            self.localized_smu = np.zeros(len(self.smu_grades))
            # count smus per panel from smu_xyz
            num_smus, panel_smu_ijks = _count_smus(panel_origin=self.panel_origin,
                                                   panel_bsize=self.panel_bsize,
                                                   panel_numblocks=self.panel_numblocks,
                                                   smu_xyz=self.smu_xyz)

        # start looping through blocks
        j = -1
        for i, prabs in enumerate(self.probabilities):

            if int(i/1000.)*1000 == i:
                print(str(i) + " blocks processed...")

            if or_corr:
                prabs  = _order_relations_correction(prabs)

            if isinstance(self.zmax, float):
                zmax = self.zmax
            else:
                zmax = self.zmax[i]

            ccdf = _discretize_cdf(z=self.cutoffs,
                                  y=prabs,
                                  zmin=self.zmin,
                                  zmax=zmax,
                                  lttype=self.lttype,
                                  ltpar=self.ltpar,
                                  uttype=self.uttype,
                                  utpar=self.utpar,
                                  discretization=self.discretization)

            if varadj < 1.0:
                if adjtype == 1:
                    ccdf = affine_correction(ccdf, varadj)
                if adjtype == 2:
                    ccdf = ilc_correction(ccdf, varadj)

            for k, cutoff in enumerate(report_cutoffs):
                if len(ccdf[ccdf >= cutoff]) > 0:
                    self.grabs[i][k] = np.average(ccdf[ccdf >= cutoff])
                    self.prabs[i][k] = float(len(ccdf[ccdf >= cutoff])) / float(self.discretization)
                else:
                    self.grabs[i][k] = 0.
                    self.prabs[i][k] = 0.

            if self.localize:
                smu_floors, smu_ceilings = _divide_smus(num_smus=num_smus[i])
                for smu_floor, smu_ceiling in zip(smu_floors, smu_ceilings):
                    j += 1
                    self.localized_smu[j] = np.average(ccdf[int(smu_floor*len(ccdf)):int(smu_ceiling*len(ccdf))])

            self.etype[i] = np.average(ccdf)
            self.cvar[i] = np.var(ccdf, ddof=1)
            self.ci[i] = np.percentile(ccdf, ci) - np.percentile(ccdf, 100. - ci)

        # Write our some stats:

        print("")
        print("")
        print("Summary Statistics:")
        print("-------------------")
        print("")
        print("Panel Average (etype) : " + str(np.round(np.average(self.etype), 3)))
        print("Panel Variance : " + str(np.round(np.var(self.etype), 3)))

        if self.localize:
            # arrange the linear smu grades ascending by ijk and then ascending by grade for each ijk
            sort_order = np.lexsort(keys=(self.smu_grades, panel_smu_ijks))
            # the original order is preserved but sorted according to the above criteria
            orig_order = np.argsort(sort_order)
            # arrange the mik smu grades according to the original order
            self.localized_smu = self.localized_smu[orig_order]
            # check the etype and localized means
            print("SMU Average : " + str(np.round(np.average(self.localized_smu), 3)))
            print("SMU Variance : " + str(np.round(np.var(self.localized_smu), 3)))

        print("Post Process Complete")

class unicond(object):

    def __init__(self, z, cutoffs=None, zmin=None, zmax=None, lttype=1, ltpar=1., uttype=1, utpar=1., discretization=1000,
                 localize=False, panel_xyz=None, smu_xyz=None, smu_grades=None,
                 panel_origin=None, panel_bsize=None, panel_numblocks=None):

        self.z = z
        self.cutoffs = cutoffs
        self.zmin = zmin
        self.zmax = zmax
        self.lttype = lttype
        self.ltpar = ltpar
        self.uttype = uttype
        self.utpar = utpar
        self.discretization = discretization
        self.localize = localize


        if self.localize:
            self.panel_xyz = panel_xyz
            self.smu_xyz = smu_xyz
            self.smu_grades = smu_grades
            if panel_origin is None or panel_bsize is None or panel_numblocks is None:
                print("Model setup not specified, estimating model setup...")
                self.panel_origin, self.panel_bsize, self.panel_numblocks = _estimate_block_definition(self.panel_xyz)
                print("Origin =", self.panel_origin, "Block Size =",self.panel_bsize, "Number of Blocks =",self.panel_numblocks)
            else:
                self.panel_origin = panel_origin
                self.panel_bsize = panel_bsize
                self.panel_numblocks = panel_numblocks

    def process(self, variogram=None):
        pass



def _estimate_block_definition(model_xyz):
    '''
    Internal Function
    Calculate the block definition for given xyz values for whole blocks (sub-block not accepted)

    Parameters
    ----------

    model_xyz: 2D array with shape (len(model_xyz, 3)

    Returns:
    --------

    origin: 1D numpy array of floats with length = 3
    Represents the bottom left corner of the block model
    blocksize: 1D numpy array of floats with length = 3
    Represents the parent blocksize in the X, Y and Z directions
    numblocks: 1D Array of integer with length = 3
    Represents the block count in each direction for the block model setup
    '''

    blocksize = np.zeros(3)
    origin = np.zeros(3)
    numblocks = np.zeros(3)

    for i in range(3):
        xv, yv = np.meshgrid(model_xyz[:, i], model_xyz[:, i])
        dists = np.abs(xv - yv)
        blocksize[i] = np.min(dists[dists!=0.])
        origin[i] = np.min(model_xyz[:, i]) - blocksize[i] / 2.0
        numblocks[i] = int((np.max(model_xyz[:, i]) - np.min(model_xyz[:, i])) / blocksize[i])

    return origin, blocksize, numblocks;

def _get_IJK_from_XYZ(x, y, z, xinc, yinc, zinc, xmorig, ymorig, zmorig):

    '''
    Internal Function
    Find the I, J, K indices from X, Y, Z points and model setup.
    Based on the Datamine IJK formulation.

    Parameters
    ----------

    x: float
    y: float
    z: float
    xinc: float
    yinc: float
    zinc: float
    xmorig: float
    ymorig: float
    zmorig: float

    Returns
    -------

    i: float
    j: float
    k: float

    Notes
    -----

    While i,j,k are actually integers, they are returned as floats as they will be used in further float calculations

    '''

    i = np.floor((x - xmorig) / xinc)
    j = np.floor((y - ymorig) / yinc)
    k = np.floor((z - zmorig) / zinc)
    return i, j, k;

def _get_IJK_from_pIJK(i, j, k, nx, ny, nz):

    '''
    Internal Function
    Calculate IJK given I, J, K indices and  number of blocks in each direction
    Based on the Datamine IJK formulation.

    Parameters
    ----------

    i: float
    j: float
    k: float
    nx: float
    ny: float
    nz: float

    Returns
    -------

    ijk: long

    Notes
    -----

    nx is not used but is included for simplicity

    '''

    return i * ny * nz + j * nz + k;

def _count_smus(panel_origin, panel_bsize, panel_numblocks, smu_xyz):

    '''
    Internal function
    Count the number of smu blocks inside each panel


    Parameters
    ----------

    panel_origin: 1D list with length = 3 containing floats
    panel_bsize: 1D list with length = 3 containing floats
    panel_numblocks: 1D list with length = 3 containing integer
    smu_xyz: 2D numpy array with shape = (len(smu_xyz), 3)

    Returns
    -------

    num_smus: 1D numpy array with length = len(np.unique(smu_xyz))
    Contains a sorted list of IJK value counts representing the number of smus in each panel
    smu_panel_ijk: 1D array with length = len(smu_xyz)
    Contains an IJK for each smu block babsed on the panel block model setup

    '''

    I, J, K = _get_IJK_from_XYZ(smu_xyz[:, 0], smu_xyz[:, 1], smu_xyz[:, 2],
                               panel_bsize[0], panel_bsize[1], panel_bsize[2],
                               panel_origin[0], panel_origin[1], panel_origin[2])
    smu_panel_ijk = _get_IJK_from_pIJK(I, J, K, panel_numblocks[0], panel_numblocks[1], panel_numblocks[2])
    xx, num_smus = np.unique(smu_panel_ijk, return_counts=True)
    num_smus = num_smus[np.argsort(xx)]
    return num_smus, smu_panel_ijk;

def _divide_smus(num_smus):

    # define a probability floor and ceiling for calculating smu grades

    step = 1. / float(num_smus)
    start = 1. / float(num_smus) * 0.5
    stop = 1.0
    smus = np.arange(start, stop, step)
    smu_floors = smus - step / 2
    smu_ceilings = smus + step / 2

    return smu_floors, smu_ceilings;

def _locate(x, xx):

    '''
    Internal function
    Return the lower index for which xx[idx] < x < xx[idx + 1]
    The array must be monotonic

    Parameters
    ----------

    x: float
    value to locate
    xx: numpy array
    array to search

    Returns
    -------

    idx: long
    Lower index.

    '''

    return np.searchsorted(xx, x);

def _gen_cdf(n):

    '''
    Internal function
    Generate an array of probabilities for n discretization points

    The probabilities start at the mid-point between 0 and the step.

    Parameters
    ----------

    n: integer
    Number of discretization points

    Returns
    -------

    y: numpy array

    '''

    step = 1. / float(n)
    start = step * (0.5)
    stop = 1.
    return np.arange(start, stop, step);

def _linearint(x, xmin, xmax, ymin, ymax):

    '''
    Internal function
    Linear interpolation for lower, middel and upper tail.

    Find probability x, given probabillties xmin, xmax for cut-offs ymin and ymax

    Parameters
    ----------

    x: float
    xmin:
    xmax:
    ymin:
    ymax:

    Returns
    -------

    y: numpy array

    '''

    return np.interp(x, [xmin, xmax], [ymin, ymax]);

def _powint(x, xmin, xmax, ymin, ymax, par):

    '''
    Power Extrapolation for lower and upper tail.

    Find probability x, given probabillties xmin, xmax for cut-offs ymin and ymax

    Parameters
    ----------

    x: float
    xmin:
    xmax:
    ymin:
    ymax:
    par:

    Returns
    -------

    y: numpy array

    '''

    return ymin + (ymax - ymin) * (((x - xmin) / (xmax - xmin)) ** (1.0 / par));

def _hyperint(x, xmin, xmax, ymin, ymax, par):

    '''
    Internal function
    Hyperbolic Extrapolation for upper tail.

    Find probability x, given probabillties xmin, xmax for cut-offs ymin and ymax

    Notes
    -----
    xmax and ymax are not used but are left as place holders for consistency with other extrapolation.

    Parameters
    ----------

    x: float
    xmin:
    xmax:
    ymin:
    ymax:
    par:

    Returns
    -------

    y: numpy array

    '''

    hyp_lambda = (ymin ** par) * (1. - xmin)
    return (hyp_lambda / (1. - x)) ** (1. / par);

def _discretize_cdf(z, y, zmin, zmax, lttype, ltpar, uttype, utpar, discretization=100):

    """
    Discretization of z values along a cdf

    Replacement of the gslib like _beyond sub-routine

    Notes:
    ------

    The upper and lower tails allow for extrapolation using models other than linear extrapolation
    Discretization between the input z values uses straight line linear interpolation.
    Use the hyperbolic model with caution as it does not require upper extrapolation limit

    Parameters
    ----------

    z: numpy array
    Usually cut-off grades
    y: numpy array
    Probabilities corresponding to the z-values
    zmin: float
    lower extrapolation limit
    zmax: float
    upper extrapolation limit
    lttype: integer
    Lower tail type; 1 = Linear, 3 = Power, 4 = Hyperbolic (*note that hyperbolic is not appropriate for lower tail)
    ltpar: float
    Lower tail parameter; To be used with the power model. <1 is positively skewed, 1 is straight line, >1 negatively
    skewed
    uttype: integer
    Upper tail type; 1 = Linear, 3 = Power, 4 = Hyperbolic
    utpar: float
    Upper tail parameter; For the power and hyperbolic models. Power parameter as per lower tail parameter. For the
    hyperbolic model, the paramter lies on interval (0,1).
    discretization: integer
    Number of discretization points/interpolated z-values along the cdf. Default = 100 but 1000 points advised,
    minimal additional computation time.

    Returns
    -------

    zz: numpy array
    Interpolated points with mean(z) and var(z) = mean(zz) and var(zz)

    """

    yy = _gen_cdf(discretization)
    zz = np.interp(yy, y, z)
    ltyy = yy[yy < y[0]]
    utyy = yy[yy >= y[-1]]

    if lttype == 3:
        ltzz = _powint(ltyy, 0., y[0], zmin, z[0], ltpar)
    elif lttype == 4:
        print('Hyperbolic model not permitted, linear model will be used')
        lttype = 1
    elif lttype == 1:
        ltzz = np.interp(ltyy, [0., y[0]], [zmin, z[0]])

    if uttype == 1:
        utzz = np.interp(utyy, [y[-1], 1.0], [z[-1], zmax])
    elif uttype == 3:
        utzz = _powint(utyy, y[-1], 1.0, z[-1], zmax, utpar)
    elif uttype == 4:
        utzz = _powint(utyy, y[-1], 1.0, z[-1], zmax, utpar)

    zz[yy < y[0]] = ltzz
    zz[yy >= y[-1]] = utzz

    return zz;

def _beyond(z, y, zmin, zmax, lttype, ltpar, uttype, utpar, discretization=100):

    """
    Discretization of z values along a cdf
    This method is not longer used as the _discretize_cdf method using broadcasting is much faster
    Similar to the approach used by the gslib beyond.f90 subroutine

    Notes:
    ------

    The upper and lower tails allow for extrapolation using models other than linear extrapolation
    Discretization between the input z values uses straight line linear interpolation.
    Use the hyperbolic model with caution as it does not require upper extrapolation limit

    Parameters
    ----------

    z: numpy array
    Usually cut-off grades
    y: numpy array
    Probabilities corresponding to the z-values
    zmin: float
    lower extrapolation limit
    zmax: float
    upper extrapolation limit
    lttype: integer
    Lower tail type; 1 = Linear, 3 = Power, 4 = Hyperbolic (*note that hyperbolic is not appropriate for lower tail)
    ltpar: float
    Lower tail parameter; To be used with the power model. <1 is positively skewed, 1 is straight line, >1 negatively
    skewed
    uttype: integer
    Upper tail type; 1 = Linear, 3 = Power, 4 = Hyperbolic
    utpar: float
    Upper tail parameter; For the power and hyperbolic models. Power parameter as per lower tail parameter. For the
    hyperbolic model, the paramter lies on interval (0,1).
    discretization: integer
    Number of discretization points/interpolated z-values along the cdf. Default = 100 but 1000 points advised,
    minimal additional computation time.

    Returns
    -------

    zz: numpy array
    Interpolated points with mean(z) and var(z) = mean(zz) and var(zz)

    """

    yy = _gen_cdf(discretization)
    zz = np.zeros(discretization)

    for i, x in enumerate(yy):
        # Are we in the lower tail
        if x < y[0]:
            tailtype = lttype
            tail_par = ltpar
            xmin = 0.
            xmax = y[0]
            ymin = zmin
            ymax = z[0]
        # Are we in the upper tail
        elif x > y[-1]:
            tailtype = uttype
            tail_par = utpar
            xmin = y[-1]
            xmax = 1.0
            ymin = z[-1]
            ymax = zmax
        # we must be in middle
        else:
            idx = _locate(x, y)
            tailtype = 1
            tail_par = utpar
            xmin = y[idx]
            xmax = y[idx + 1]
            ymin = z[idx]
            ymax = z[idx + 1]

        if tailtype == 1:
            zz[i] = _linearint(x, xmin, xmax, ymin, ymax)
        if tailtype == 3:
            zz[i] = _powint(x, xmin, xmax, ymin, ymax, tail_par)
        if tailtype == 4:
            zz[i] = _hyperint(x, xmin, xmax, ymin, ymax, tail_par)

    return zz;

def _order_relations_correction(y):

    """
    Internal function
    Order Relations Correction (for MIK).
    Forces probabilities to be monotonic.

    Parameters
    ----------

    y: numpy array
    Probabilities to be corrected.

    Returns
    -------

    y: numpy array

    """
    # probabilities must fall within bounds (0,1)
    y[-1] = np.max([y[-1], 0])
    y[0] = np.min([y[0], 1])
    upward = y
    downward = y

    for i in range(len(y)):
        # upward
        if i != len(upward) - 1:

            if upward[i] < upward[i + 1]:
                upward[i] = upward[i + 1]
        # downward
        j = len(downward) - 1 - i
        if j != 0:
            if downward[j] > downward[j - 1]:
                downward[j] = downward[j - 1]
    return np.average([upward, downward], axis=0);

def affine_correction(z, varadj):
    """
    Affine Support Correction

    Parameters
    ----------

    z: numpy array
    An array of grades to be corrected. in the case of the mik the grades are from the panel conditional
    distribution
    vared: float
    Variance reduction factor (1 - gammabar)

    Returns
    -------

    qprime: numpy array

    Examples
    --------

    >> z = [0.1 0.3, 0.5]
    >> varadj = 1.0 # 1.0 corresponds to no adjustment
    >> pyrpa.nonlinear.affine_correction(z, varadj)
    >> (0.1, 0.3, 0.5)

    """

    m = np.average(z)
    return (varadj**0.5)*(z - m) + m;

def ilc_correction(z, varadj):
    """
    Indirect Lognormal Correction

    From Neufield and Leuangthong "Calculation of Recoverable Reserves"

    Parameters
    ----------

    z: numpy array
    An array of grades to be corrected. in the case of the mik the grades are from the panel conditional
    distribution
    vared: float
    Variance reduction factor (1 - gammabar)

    Returns
    -------

    qprime: numpy array

    Examples
    --------

    >> z = [0.1 0.3, 0.5]
    >> varadj = 1.0 # 1.0 corresponds to no adjustment
    >> pyrpa.nonlinear.ilc_correction(z, varadj)
    >> (0.1, 0.3, 0.5)

    """
    if np.sum(z) > 0.:
        m = np.average(z)
        cv = m / np.std(z, ddof=1)
        b = (np.log((varadj * cv**2 + 1)) / np.log(cv**2 + 1))**0.5
        a = (m / (varadj * cv**2 + 1)**0.5) * (((cv**2 + 1)**0.5) / m) ** b
        q = a * z**b
        mq = np.average(q)
        q_prime = q *(m / mq)
    else:
        q_prime = np.zeros(len(z))
    return q_prime;


