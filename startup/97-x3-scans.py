
def tscan_xpress3(name:str, comment:str, n_cycles:int=1, delay:float=0, **kwargs):
    """
    Trajectory Scan - Runs the monochromator along the trajectory that is previously loaded in the controller N times
    Parameters
    ----------
    name : str
        Name of the scan - it will be stored in the metadata
    n_cycles : int (default = 1)
        Number of times to run the scan automatically
    delay : float (default = 0)
        Delay in seconds between scans
    Returns
    -------
    uid : list(str)
        Lists containing the unique ids of the scans
    See Also
    --------
    :func:`tscanxia`
    """
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    #uids = []
    RE.is_aborted = False
    for indx in range(int(n_cycles)):
        if RE.is_aborted:
            return 'Aborted'
        if n_cycles == 1:
            name_n = name
        else:
            name_n = name + ' ' + str(indx + 1)
        print('Current step: {} / {}'.format(indx + 1, n_cycles))

        RE(prep_traj_plan())
        uid = RE(xpress3.start_acquisition())
        print(uid)
        #uid, = RE(execute_trajectory(name_n, comment=comment))
        #yield uid
        #uids.append(uid)
        time.sleep(float(delay))
    print('Done!')
    #return uids