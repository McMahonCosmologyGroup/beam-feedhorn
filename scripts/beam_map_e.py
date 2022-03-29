"""
Beam Mapping script.
Scans source in XY plane and records amplitude and phase at each point.
Grace E. Chesmore, Feb 2022

All stage commands are commented out to make this adaptable for other stage setups.
"""
import datetime
import logging
import os
import platform
import time
import serial
import casperfpga
import holog_daq
import numpy as np
import plot_func
from holog_daq import fpga_daq3, poco3, synth3

is_py3 = int(platform.python_version_tuple()[0]) == 3
SynthOpt = synth3.SynthOpt

ser = serial.Serial('/dev/ttyUSB0')

def beam1d(fre, angle, step):

    # Begin with source centered above the LATRt window.
    # Then define this spot to the stages as (0,0) "center".

    # stage_xy.position = [0,0]

    now = datetime.datetime.now()
    today = str(now.day) + "-" + str(now.month) + "-" + str(now.year)

    N_MULT = 18
    F_START = int(fre * 1000.0 / N_MULT)  # in MHz
    F_STOP = F_START
    SynthOpt.F_OFFSET = 5  # in MHz
    freq = F_STOP

    # SynthOpt.IGNORE_PEAKS_BELOW = int(986)
    # SynthOpt.IGNORE_PEAKS_ABOVE = int(990)
    SynthOpt.IGNORE_PEAKS_BELOW = int(738)
    SynthOpt.IGNORE_PEAKS_ABOVE = int(740)

    DELTA_T_USB_CMD = 0.5
    T_BETWEEN_DELTA_F = 0.5
    T_BETWEEN_SAMP_TO_AVG = 0.5
    T_TO_MOVE_STAGE = 1
    DELTA_T_VELMEX_CMD = 0.25

    DELTA_X_Y = 1
    X_MIN_ANGLE = -angle
    X_MAX_ANGLE = angle
    Y_MIN_ANGLE = 0
    Y_MAX_ANGLE = 0
    PHI_MIN_ANGLE = 0
    PHI_MAX_ANGLE = 0
    DELTA_PHI = 90

    fpga_daq3.RoachOpt.N_CHANNELS = 21

    N_PTS = (X_MAX_ANGLE - X_MIN_ANGLE) / DELTA_X_Y + 1

    prodX = prodY = prodPHI = 0
    if X_MIN_ANGLE == X_MAX_ANGLE:
        prodX = 1
    else:
        prodX = int(abs(X_MAX_ANGLE - X_MIN_ANGLE) / DELTA_X_Y + 1)
    if Y_MIN_ANGLE == Y_MAX_ANGLE:
        prodY = 1
    else:
        prodY = int(abs(Y_MAX_ANGLE - Y_MIN_ANGLE) / DELTA_X_Y + 1)
    if PHI_MIN_ANGLE == PHI_MAX_ANGLE:
        prodPHI = 1
    else:
        prodPHI = 1  # int(abs(PHI_MAX_ANGLE - PHI_MIN_ANGLE)/DELTA_PHI + 1)

    nsamp = int(prodX * prodY * prodPHI)

    print("nsamp = " + str(nsamp))
    STR_FILE_OUT = (
        "../Data/" + str(fre) + "GHz_" + str(angle) + "deg_1D_E_" + today + ".txt"
    )
    arr2D_all_data = np.zeros(
        (nsamp, (4 * fpga_daq3.RoachOpt.N_CHANNELS + 7))
    )  # , where the 7 extra are f,x,y,phi,... x_cur,y_cur, index_signal of peak cross power in a single bin (where phase is to be measured)

    def MakeBeamMap(i_f, f, LOs, baseline, fpga):
        i = 0

        ser.write(str.encode("E"))

        print("begin MakeBeamMap() for f = " + str(f))
        synth3.set_f(0, f, LOs)
        synth3.set_f(1, f + SynthOpt.F_OFFSET, LOs)

        arr_phase = np.zeros((fpga_daq3.RoachOpt.N_CHANNELS, 1))
        arr_aa = np.zeros((fpga_daq3.RoachOpt.N_CHANNELS, 1))
        arr_bb = np.zeros((fpga_daq3.RoachOpt.N_CHANNELS, 1))
        arr_ab = np.zeros((fpga_daq3.RoachOpt.N_CHANNELS, 1))
        index_signal = 0

        print(" move x to minimum angle")
        if X_MIN_ANGLE != 0:
            ser_x_min = ('I1M-' + str(80*abs(X_MIN_ANGLE)) +',R') 
            ser.write(str.encode(ser_x_min)) #Move motor 1 (our x axis) by X_MIN_ANGLE degrees.
            time.sleep(abs( 0.25*X_MIN_ANGLE))
            ser.write(str.encode('C'))
            time.sleep(DELTA_T_VELMEX_CMD)

        speed = ('S1M200,S2M200,R')
        ser.write(str.encode(speed))
        time.sleep(1)
        ser.write(str.encode('C'))

        y = 0
        phi = 90

        for x in np.linspace(X_MIN_ANGLE, X_MAX_ANGLE, int(N_PTS)):

            print(
                " Recording data: f: "
                + str(f)
                + "), x: ("
                + str(int(x))
                + "/"
                + str(int(X_MAX_ANGLE))
                + "), y: ("
                + str(int(y))
                + "/"
                + str(int(Y_MAX_ANGLE))
                + ")"
            )
            arr_aa, arr_bb, arr_ab, arr_phase, index_signal = fpga_daq3.TakeAvgData(
                baseline, fpga, SynthOpt
            )
            arr2D_all_data[i] = (
                [f]
                + [x]
                + [y]
                + [x] # extra indices to hold motor read-out positions (if available)
                + [y] # extra indices to hold motor read-out positions (if available)
                + [phi]
                + [index_signal]
                + arr_aa.tolist()
                + arr_bb.tolist()
                + arr_ab.tolist()
                + arr_phase.tolist()
            )
            i = i + 1
            print(str(i) + "/" + str(nsamp))

            if x < X_MAX_ANGLE:
                print("moving x forward")
                if abs(DELTA_X_Y) != 0:
                    ser.write(str.encode('I1M' + str(abs(80*DELTA_X_Y)) +',R'))   # moves phi-axis 80*DELTA_phi degrees
                    time.sleep(T_TO_MOVE_STAGE)
                    ser.write(str.encode('C')) #Clear all commands from currently selected program. 
                    time.sleep(DELTA_T_VELMEX_CMD)

        time.sleep(DELTA_T_VELMEX_CMD)
        speed = ('S1M1500,S2M1500,R')
        ser.write(str.encode(speed))
        time.sleep(1)
        ser.write(str.encode('C'))
        print(' returning x home')
        if abs(X_MAX_ANGLE) != 0: 
            ser_x_max = ('I1M-' + str(80*abs(X_MAX_ANGLE) ) +',R') #Before this command, y = Y_MIN_ANGLE, so I need to go forward Y_MIN_ANGLE degrees to make it back home. 
            ser.write(str.encode(ser_x_max))
            time.sleep(abs(0.25*abs(X_MIN_ANGLE)))
            ser.write(str.encode('C')) #Clear all commands from currently selected program. 
            time.sleep(DELTA_T_VELMEX_CMD)

        time.sleep(DELTA_T_VELMEX_CMD)
        print(' end f = '+str(f))

    f_sample = F_START
    print("Begining map where frequency = " + str(fre) + "GHz.")
    time.sleep(T_BETWEEN_DELTA_F)
    # Now is time to take a beam map
    MakeBeamMap(0, f_sample, LOs, baseline, fpga)
    print("Beam Map Complete.")

    arr2D_all_data = np.around(arr2D_all_data, decimals=3)
    print("Saving data...")
    np.savetxt(
        STR_FILE_OUT,
        arr2D_all_data,
        fmt="%.3e",
        header=(
            "f_sample(GHz), x, y, phi, index_signal of peak cross power, and "
            + str(fpga_daq3.RoachOpt.N_CHANNELS)
            + " points of all of following: aa, bb, ab, phase (deg.)"
        ),
    )

    return STR_FILE_OUT
def init_fpga_test():
    # START OF MAIN:
    fpga = None
    roach, opts, baseline = fpga_daq3.roach2_init()

    loggers = []
    lh = poco3.DebugLogHandler()
    logger = logging.getLogger(roach)
    logger.addHandler(lh)
    logger.setLevel(10)

    ########### Setting up ROACH Connection ##################
    ##########################################################
    print("------------------------")
    print("Programming FPGA with call to a python2 prog...")

    err = os.system("/opt/anaconda2/bin/python2 upload_fpga_py2.py")
    assert err == 0

    print("Connecting to server %s ... " % (roach)),
    if is_py3:
        fpga = casperfpga.CasperFpga(roach)
    else:
        fpga = casperfpga.katcp_fpga.KatcpFpga(roach)
    time.sleep(1)

    if fpga.is_connected():
        print("ok\n")
    else:
        print("ERROR connecting to server %s.\n" % (roach))
        poco3.exit_fail(fpga)
    ##########################################################
    ##########################################################

    LOs = synth3.get_LOs()
    # Turn on the RF output. (device,state)
    synth3.set_RF_output(0, 1, LOs)
    synth3.set_RF_output(1, 1, LOs)
    return roach,opts,baseline,LOs,fpga

roach,opts,baseline,LOs,fpga = init_fpga_test()

span = 45 #degrees
res = 1 # step size in degrees
save_fig=1

freq = np.linspace(230,270,41)

for ii in range(len(freq)):
    str_out = beam1d(freq[ii], span, res)
    plot_func.beam_plot_1D(str_out,save_fig)