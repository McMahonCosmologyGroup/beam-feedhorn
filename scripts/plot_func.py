import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from numpy import genfromtxt
from holog_daq import fpga_daq3

matplotlib.rcParams["font.size"] = 16
matplotlib.rcParams.update({"axes.grid" : True, "grid.color": "grey", "grid.alpha": .2, 'xtick.direction':'in','ytick.direction':'in'})

def beam_plot_1D(txt_file,save):

        data=np.loadtxt(txt_file)
        ang=(len(data)-1) /2
        ang=np.linspace(-ang,ang,len(data))
        L_MEAN = 1
        N_INDIV = 7
        L=len(data[0,:])

        line_size = np.size(data[0])
        nsamp =  np.size(data,0)
        arr_f = np.zeros(nsamp)
        arr_x = np.zeros(nsamp)
        arr_y = np.zeros(nsamp)
        arr_phi = np.zeros(nsamp)
        amp_cross=np.zeros(nsamp)
        amp_phase=np.zeros(nsamp)
        amp_var=np.zeros(nsamp)
        phase=np.zeros(nsamp)

        i_AA_begin = int(N_INDIV + (1-1)*(line_size-N_INDIV)/4)
        i_AA_end= int(N_INDIV + (2-1)*(line_size-N_INDIV)/4) -1
        i_BB_begin = int(N_INDIV + (2-1)*(line_size-N_INDIV)/4)
        i_BB_end= int(N_INDIV + (3-1)*(line_size-N_INDIV)/4) -1
        i_AB_begin = int(N_INDIV + (3-1)*(line_size-N_INDIV)/4)
        i_AB_end= int(N_INDIV + (4-1)*(line_size-N_INDIV)/4) -1
        i_phase_begin = int(N_INDIV + (4-1)*(line_size-N_INDIV)/4)
        i_phase_end= int(N_INDIV + (5-1)*(line_size-N_INDIV)/4) -1

        arr_f = data[:,0]
        arr_x = data[:,1]
        arr_y = data[:,2]
        arr_phi = data[:,3]
        index_signal = data[:,4]

        for kk in range(nsamp):
            #take in raw DATA
            arr_AA = np.array(fpga_daq3.running_mean(data[kk][i_AA_begin : i_AA_end],L_MEAN))
            arr_BB = np.array(fpga_daq3.running_mean(data[kk][i_BB_begin : i_BB_end],L_MEAN))
            arr_AB = np.array(fpga_daq3.running_mean(data[kk][i_AB_begin : i_AB_end],L_MEAN))
            arr_phase = np.array( data[kk][i_phase_begin : i_phase_end] )
            n_channels = np.size(arr_AB)

            #make amplitude arrays, in case they need to be plotted.
            amp_cross[kk] = arr_AB[int(n_channels/2)]
            amp_var[kk] = np.power( np.divide(arr_AB[int(n_channels/2)],arr_AA[int(n_channels/2)]) , 2)
            amp_phase[kk] = np.remainder(arr_phase[int(n_channels/2)],360.)

        theta_arr = arr_x if arr_x[0] != 0 else arr_y
        fig,axes = plt.subplots(1,2,figsize = (14,5))
        axes[0].plot(theta_arr,20*np.log10(amp_var/np.max(amp_var)))
        axes[0].set_xlabel(r"$\theta$ [deg.]")
        axes[1].set_xlabel(r"$\theta$ [deg.]")
        axes[0].set_ylabel(r"Power [dB]")
        axes[1].set_ylabel(r"Phase [deg.]")
        axes[0].set_title(r"Amplitude")
        axes[1].set_title(r"Phase")
        axes[1].plot(theta_arr,amp_phase)
        plt.tight_layout(w_pad=0.7)
        if save==1:
            plt.savefig(txt_file[:-4]+".png")
        # plt.show()


