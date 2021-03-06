#!/usr/bin/env python

''' Maps the real-valued resource shares in mu on integer-valued m_k over N subcarriers and T slots. See my academic paper in JSAC for details.
 Input:
       - mu is size(1,users+dtx). sum(mu) == 1. 
       - N is the number of subcarriers. e.g. 50 on 10 MHz
       - T is the number of timeslots to consider, e.g. 20 in an LTE frame
 
 Output: 
       - outMap is size(T, K). For each user and slot it contains the
       number of resource blocks assigned. sum(sum(outMap)) == N*(T-t_sleep).

File: quantmap.py
'''

__author__ = "Hauke Holtkamp"
__credits__ = "Hauke Holtkamp"
__license__ = "unknown"
__version__ = "unknown"
__maintainer__ = "Hauke Holtkamp"
__email__ = "h.holtkamp@gmail.com" 
__status__ = "Development" 

from numpy import *

def quantmap(alloc, N, T):
    """Fit alloc to N x T with some rounding. Output is how many resources each user should receive in each timeslot."""

    rbmap = empty([N, T])
    rbmap[:] = nan
    alloc = array(alloc) # just in case

    K = alloc.size-1 # users

    # Initial mapping over all RB
    if N*T*alloc[-1] >= K: # Otherwise sleep duration would be negative

        t_sleep  = floor( (N * T * alloc[-1] - K ) / N )
        t_active = T - t_sleep
        m_k = ceil(  alloc[:-1] * N * T   )
        leftoverRBs = N*T - sum(m_k) - t_sleep * N
        
    else: #% high load. N*T*mu(end) < K
        t_sleep = 0
        t_active = T
        m_k = floor(  alloc[:-1] * N * T  ) 
        leftoverRBs = N*T - sum(m_k)

    # add remaining RBs to users round robin
    # set index here so the round robin continues where it left off within the while loop. 
    rnd = random.permutation(K) # random starting point
    index = rnd[0] # Can this be done in one line with the one above?
        
    
    # Note that it's possible that a user receives RBs who did not request any since we are overcompensating
    while leftoverRBs > 0:
        m_k[index] = m_k[index] + 1
        leftoverRBs = leftoverRBs - 1
        index = mod(index+1, K)  # move to next user

    m_k_start = m_k # save value for comparison later

    # Mapping per slot (from budget)
    m_slot = empty([t_active, K])
    m_slot[:] = nan
    # for each active time slot

    # set index here so the round robin continues where it left off within the while loop. 
    indx = rnd[0] # Can this be done in one line with the one above?
    for slot in arange(t_active):
        # take first guess at allocation by floor()
        m_slot[slot, :] = floor( m_k/sum(m_k) * N )

        # fill up the remaining 
        remainder = N - sum(m_slot[slot, :])
        while remainder > 0:
            if nansum(m_slot[:,indx]) < m_k_start[indx]: # only if there is room. otherwise there may be negative slot numbers
                m_slot[slot, indx] = m_slot[slot, indx] + 1
                remainder = remainder - 1
            indx = mod(indx+1, K)  # move to next user

        # keep track
        m_k = m_k - m_slot[slot, :]

        # test validity
        if nansum( m_k + nansum( m_slot,axis=0)) != N * t_active:
            disp('Sum mismatch in quantMap.m!')

    # test validity
    if (sum(m_slot,axis=0) != m_k_start).all():
        raise ValueError ('Assignment faulty in quantMap.m!')
    if any(m_slot<0):
        raise ValueError ('Negative assignment in quantMap.m!')

    outMap = empty([T, K])
    outMap[:] = nan # sleep slots will remain nan
    outMap[:t_active, :] = m_slot

    return outMap
