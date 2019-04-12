print(__file__)
import bluesky.plans as bp
import os
import sys


def tscan(name:str, comment:str, n_cycles:int=1, delay:float=0, **kwargs):
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
        uid, = RE(execute_trajectory(name_n, comment=comment))
        yield uid
        #uids.append(uid)
        time.sleep(float(delay))
    print('Done!')
    #return uids


def general_scan(detectors, num_name, den_name, result_name, motor, rel_start, rel_stop, num, find_min_max, retries, **kwargs):
    sys.stdout = kwargs.pop('stdout', sys.stdout)
    for index, detector in enumerate(detectors):
        if type(detector) == str:
            detectors[index] = eval(detector)

    if type(motor) == str:
        motor = eval(motor)

    print('[General Scan] Starting scan...')
    ax = kwargs.get('ax')

    if find_min_max:
        over = 0
        while(not over):
            uid, = RE(general_scan_plan(detectors, motor, rel_start, rel_stop, int(num)), NormPlot(num_name, den_name, result_name, result_name, motor.name, ax=ax))
            yield uid
            last_table = db.get_table(db[-1])
            if detectors[0].polarity == 'pos':
                index = np.argmax(last_table[num_name])
            else:
                index = np.argmin(last_table[num_name])
            motor.move(last_table[motor.name][index])
            print('[General Scan] New {} position: {}'.format(motor.name, motor.position))
            if (num >= 10):
                if (((index > 0.2 * num) and (index < 0.8 * num)) or retries == 1):
                    over = 1
                if retries > 1:
                    retries -= 1
            else:
                over = 1
        print('[General Scan] {} tuning complete!'.format(motor.name))
    else:
        uid, = RE(general_scan_plan(detectors, motor, rel_start, rel_stop, int(num)), NormPlot(num_name, den_name, result_name, result_name, motor.name, ax=ax))
        yield uid
    print('[General Scan] Done!')


def get_offsets(num:int = 20, *args, **kwargs):
    """
    Get Ion Chambers Offsets - Gets the offsets from the ion chambers and automatically subtracts from the acquired data in the next scans

    Parameters
    ----------
    num : int
        Number of points to acquire and average for each ion chamber


    Returns
    -------
    uid : list(str)
        List containing the unique id of the scan


    See Also
    --------
    :func:`tscan`
    """
    sys.stdout = kwargs.pop('stdout', sys.stdout)

    adcs = list(args)
    if not len(adcs):
        raise ValueError("Error, no adcs supplied (please define your detector_dictionary")

    old_avers = []
    for adc in adcs:
        old_avers.append(adc.averaging_points.get())
        adc.averaging_points.put(4)
        #adc.averaging_points.put(15)
    
    uid, = RE(get_offsets_plan(adcs, num = int(num)))

    if 'dummy_read' not in kwargs:
        print('Updating values...')

    arrays = []
    offsets = []
    df = db.get_table(db[-1])
    for index, adc in enumerate(adcs):
        key = '{}_volt'.format(adc.name)
        array = df[key]
        offset = np.mean(df[key][2:int(num)])

        arrays.append(array)
        offsets.append(offset)
        if 'dummy_read' not in kwargs:
            adc.offset.put(offset)
            print('{}\nMean ({}) = {}'.format(array, adc.dev_name.value, offset))
        adc.averaging_points.put(old_avers[index])
    
    run = db[uid]
    for i in run['descriptors']:
        if i['name'] != 'primary':
            filename = i['data_keys'][i['name']]['filename']
            if os.path.isfile(filename):
                os.remove(filename)

    if 'dummy_read' in kwargs:
        print_message = ''
        for index, adc in enumerate(adcs):
            print('Mean ({}) = {}'.format(adc.dev_name.value, offsets[index]))

            saturation = adc.dev_saturation.value

            if adc.polarity == 'neg':
                if offsets[index] > saturation/100:
                    print_message += 'Increase {} gain by 10^2\n'.format(adc.dev_name.value)
                elif offsets[index] <= saturation/100 and offsets[index] > saturation/10:
                    print_message += 'Increase {} gain by 10^1\n'.format(adc.dev_name.value)
        print('-' * 30)
        print(print_message[:-1])
        print('-' * 30)

    sys.stdout = kwargs.pop('stdout', sys.stdout)
    print(uid)
    print('Done!')
    yield uid
