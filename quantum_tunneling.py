import numpy as np 
import matplotlib.pyplot as plt 
import os

from numba import njit
import numba
#solve the eigenvalue problem and get the time-dependent wavefunction  

@njit() 
def integral(f,dx,axis = 0):
    #This function allows us to approximate integrals in discrete space
    return np.sum(f*dx, axis = axis)

os.makedirs('images',exist_ok=True)

def fourier_transform(psi, x, E, dx):
    k = [np.sqrt(2*E[i]) for i,x in enumerate(x[1:-1])]
    psi_fourier = (1/np.sqrt(2*np.pi))*integral(np.exp(-1j*np.real(k)*x[1:-1])*psi, dx)
    return psi_fourier, k


def plot(x, L, Psi, Psi_norm, V_flat, t, psi_1_prob, psi_2_prob, psi_3_prob):
    fig = plt.figure(figsize = (12, 8), dpi = 50, facecolor='black')
    ax = plt.axes(xlim=(0, L), ylim=(-0.25, 0.25))
    ax.plot([], [], lw=2)
    ax.plot(x,V_flat, label = '$V(x)$',c='orange')
    ax.fill_between(x,0,V_flat,color="orange",alpha=0.8)

    ax.set_title('Gaussian wave packet with a potential barrier', fontsize = 20)
    
    ax.plot(x,np.real(Psi),color="red",label = r'$Re(\psi)$',zorder=5)
    #ax.fill_between(x,0,np.real(Psi),color="red",alpha=0.9)
    
    ax.plot(x,np.imag(Psi),color="aqua", label = r'$Im(\psi)$',zorder=5)
    #ax.fill_between(x,0,np.imag(Psi),color="aqua",alpha=0.9)        
        
    ax.plot(x,Psi_norm,color="green",  lw = 3, label = r'$|\psi|^2$',zorder=6)
    #ax.fill_between(x,0,np.real(Psi_norm),color="white",alpha=0.2,zorder=1)
    #ax.fill_between(x,0,-np.real(Psi_norm),color="white",alpha=0.2,zorder=1)



    ax.legend(fontsize = 15)
    ax.set_xlabel('$x$', fontsize = 15)
    ax.set_facecolor("black")

    ax.text(10,0.3,f"Time: {t}", color="white", fontsize = 20)
    ax.text(10,0.26,"Prob(left):  %.3f" % np.real(psi_1_prob),color="white", fontsize=18)
    ax.text(10,0.23,"Prob(mid):  %.3f" % np.real(psi_2_prob),color="white", fontsize=18)
    ax.text(10,0.20,"Prob(right): %.3f" % np.real(psi_3_prob),color="white", fontsize=18)
    ax.text(10, -0.21, "Prob(Total): %.1f" % np.real(psi_1_prob+psi_2_prob+psi_3_prob), color="white", fontsize=20)

    plt.tight_layout()
    plt.axis('off')
    #plt.savefig(f'images\{t}.png')
    plt.show()

@njit() 
def normalize(H,dx):
    E, psi = np.linalg.eigh(H)
    psi = psi.T
    norm = integral(np.abs(psi)**2, dx)
    psi = psi/np.sqrt(norm)
    return psi, E


@njit()
def get_C_n(psi, Psi0, dx, N_grid):
    
    #get expansion coeffs
    c_n = np.zeros_like(psi[0],dtype=numba.complex64)
    for j in range(0, N_grid-1):
        c_n[j] = integral(np.conj(psi[j]) * Psi0, dx) #for each eigenvector, compute the inner product


    return c_n

def wavepacket(N_grid, L, a, V0, w, x0, k0,sigma,t):
        
    x = np.linspace(0,L,N_grid+1) #grid of points
    dx = x[1]-x[0] #grid point spacing or 'discrete' analogue of the differential length

    Psi0  = np.exp( -1/2* (x[1:-1]-x0)**2/sigma**2) *np.exp(1j*k0*x[1:-1]) #+ np.exp( -1/2* (x[1:-1]-520)**2/sigma**2) *np.exp(-1j*k0*x[1:-1]) 
    #use this range for x because as mentionned, we need the wavefunction to be 0 at the endpoints of the grid. 
    
    #normalise the initial state
    norm  = integral(np.abs(Psi0)**2,dx)
    Psi0 = Psi0/np.sqrt(norm)        
    
    #potential as a flat array
    V_flat = np.array([V0 if a< pos < a+w else 0 for pos in x[1:-1]])
    #V_flat_1 = np.array([V0 if 0 < pos < x[-1] else 0 for pos in x[1:-1]])
    #V_flat_2 = np.array([V0 if a+6*w< pos < a+7*w else 0 for pos in x[1:-1]])
    #V_flat = V_flat_1 + V_flat_2
    
    #V_flat = np.array([(2/np.cosh(abs(pos-a)))**2 if a< pos < a+5*w else 0 for pos in x[1:-1]])
    #potential energy as a diagonal matrix
    V = np.diag(V_flat)    

    #kinetic energy
    T = -1/2 * 1/dx**2 * (np.diag(-2*np.ones(N_grid-1))+ np.diag(np.ones(N_grid-2),1)+ np.diag(np.ones(N_grid-2),-1))
    #print(T.shape)
    #Hamiltonian
    H = T+V
    
    
    for i in range(0,t,50):
        #get eigenvalues and eigenvectors and normalise
        psi, E = normalize(H, dx)

        c_n = get_C_n(psi, Psi0, dx, N_grid)
        #get a function that returns the time dependent wavefunction
        Psi = np.dot(psi.T, (c_n*np.exp(-1j*E*i))) 
        
        Psi_norm = np.conj(Psi)*Psi
        Psi_norm = Psi_norm/np.sqrt(Psi_norm)
        psi_1 = np.array([Psi[j] if a > pos else 0 for j,pos in enumerate(x[1:-1])])
        psi_2 = np.array([Psi[j] if a < pos < a+w else 0 for j,pos in enumerate(x[1:-1])])
        psi_3 = np.array([Psi[j] if a < pos else 0 for j,pos in enumerate(x[1:-1])])
        psi_1_prob = integral(np.conj(psi_1)*psi_1, dx).real
        psi_2_prob = integral(np.conj(psi_2)*psi_2, dx).real
        psi_3_prob = integral(np.conj(psi_3)*psi_3, dx).real

        x_expected = integral(np.conj(Psi)*x[1:-1]*Psi, dx).real
        #print(x_expected)
        
        plot(x[1:-1], L, Psi, Psi_norm, V_flat, i, psi_1_prob, psi_2_prob, psi_3_prob)
        #plt.text(10,0.5,f"{i}",fontsize = 20,color="black")
        #plt.show()


wave = wavepacket(N_grid=500,L=600,a=300, V0=0.12, w=10, x0=80, k0=0.5, sigma=20, t=10000)
