def intervals_1d(arr1d):
    """
    Calculate min, max and mean inter-fire interval and count of <= 3 year inter-fire intervals
    """
    #indices of years with fire occurrence
    ivals = arr1d.nonzero()[0]

    #shift & subtract indices to derive intervals
    diffs=ivals[1:] - ivals[:-1]
    try:
        imin=diffs.min()       #Min inter-fire interval
        imax=diffs.max()       #Max inter-fire interval
        imean=diffs.mean()       #Mean inter-fire interval
        ile3=(diffs<=3).sum()  #No. fires with <= 3 year inter-fire interval
    except ValueError: #diffs == array([])
        imin=0
        imax=0
        imean=0
        ile3=0

    return imin, imax, imean, ile3

def intervals(arr3d):
    """
    Calculate min, max and mean inter-fire interval and count of <= 3 year inter-fire intervals
    """
    
    s = arr3d.shape
    arr2d = arr3d.reshape((s[0], s[1] * s[2]))

    #indices of years with fire occurrence
    ivals = arr2d.nonzero()[0]
    ivals.shape = (ivals.shape[0] // (s[1] * s[2]), s[1] * s[2])

    #shift & subtract indices to derive intervals
    diffs=ivals[1:] - ivals[:-1]
    try:
        imin=diffs.min(axis=0)       #Min inter-fire interval
        imax=diffs.max(axis=0)       #Max inter-fire interval
        imean=diffs.mean(axis=0)     #Mean inter-fire interval
        ile3=(diffs<=3).sum(axis=0)  #No. fires with <= 3 year inter-fire interval
        imin.shape = imax.shape = ile3.shape=s[1:]

    except ValueError: #diffs == array([])
        imin=imax=imean=ile3=np.zeros(shape=s[1:])

    return imin, imax, imean, ile3
