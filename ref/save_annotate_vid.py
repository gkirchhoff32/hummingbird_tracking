import math
import imageio
import numpy as np
import cv2
from os.path import join as oj
import os
import subprocess
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx
from sklearn.cluster import KMeans

data_folder = '/Users/chandan/drive/research/hummingbird_tracking/data'
# cap = cv2.VideoCapture(oj(data_folder, 'side', 'ama.mov'))
# cap = cv2.VideoCapture(oj(data_folder, 'side', 'cor.mov'))
cap = cv2.VideoCapture(oj(data_folder, 'top', 'clip_full_fit.mp4'))
fgbg = cv2.createBackgroundSubtractorMOG2()

f_width, f_height = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
if os.path.exists('out.avi'):
    os.remove('out.avi')

max_frames = 10
ret = True 
frame_num = 0
vid_out = np.zeros((max_frames, f_height, f_width))
thetas = []
rhos = []
while(ret and frame_num < max_frames):
    ret, frame = cap.read()
    fgmask = fgbg.apply(frame)
    lines = cv2.HoughLines(fgmask, 1, np.pi / 180, 100) # 200 is num_votes
    # print('len lines', len(lines))
    theta_t = []
    rho_t = []
    for line_num in range(40):
        for rho,theta in lines[line_num]:
            a = np.cos(theta)
            b = np.sin(theta)
            x0 = a*rho
            y0 = b*rho
            x1 = int(x0 + 1000*(-b))
            y1 = int(y0 + 1000*(a))
            x2 = int(x0 - 1000*(-b))
            y2 = int(y0 - 1000*(a))
            theta_t.append(theta)
            rho_t.append(rho)
        cv2.line(fgmask,(x1,y1),(x2,y2),(255, 255, 255),2) 
    thetas.append(theta_t)
    rhos.append(rho_t)
    vid_out[frame_num] = fgmask
    cv2.imshow('frame', fgmask)
    '''
    k = cv2.waitKey(30) & 0xff # waitKey is time in ms
    if k == 27:
        break
    '''
    frame_num += 1

print('writing...')
imageio.mimwrite('out.mp4', vid_out, fps=20)
for frame_num in range(10):
    imageio.imwrite('frame_' + str(frame_num) + '.jpg', vid_out[frame_num, :, :])
cap.release()
cv2.destroyAllWindows()


# plot vars (num_times x num_lines) 
thetas = np.array(thetas) * 360 / (2 * math.pi)
rhos = np.array(rhos)
mean_thetas = []
thetas[rhos<0] = -1 * (180 - thetas[rhos<0])  # altering thetas here
mean_thetas = []
mean_thetas = []
print('num <0', np.sum(rhos<0))
print('num_times, num_lines', thetas.shape)
# print(thetas)
all_vars = [rhos, thetas]
for var_num in range(2):
    mean_thetas = []
    var = all_vars[var_num]
    (num_times, num_lines) = var.shape
    cm_subsection = np.linspace(0, 1, num_lines) 
    colors = [ cmx.jet(x) for x in cm_subsection ]
    fig = plt.figure(figsize=(14, 6))
    km = KMeans(n_clusters=2, random_state=0)
    for line_num in range(num_lines):
        plt.plot(range(num_times), var[:, line_num], 'o', label=str(line_num), alpha = 0.3, color = colors[line_num])
        pass
    for t in range(num_times):    
        km.fit(var[t, :].reshape(-1, 1))
        # print(km.cluster_centers_.shape)
        for m in range(km.cluster_centers_.shape[0]):
            plt.plot(t, km.cluster_centers_[m], 'o', color='black', alpha=1, markersize=10)
        mean_thetas.append(km.cluster_centers_)
    plt.grid(True)
    plt.xticks(range(num_times))
    plt.xlim((0, max_frames))
         
    # plt.legend()
    if var_num  == 0:
        plt.savefig('rhos.png')
    else:
        plt.savefig('thetas.png')
mean_thetas = np.array(mean_thetas)
print('mean_thetas.shape', mean_thetas.shape)
for i in range(num_times):
    if mean_thetas[i, 0] * mean_thetas[i, 1] < 0: # want one angle to be neg, one pos
        continue
    else:
        mean_thetas[i, 1] = (180 - mean_thetas) # if replace the smaller angle, measurement gets much bigger, if we replace the bigger angle measurement gets much smaller
theta_out = np.abs(mean_thetas[:, 0] - mean_thetas[:, 1])

fig = plt.figure(figsize=(14, 6))
plt.plot(range(num_times), theta_out, 'o')
plt.grid(True)
plt.xticks(range(num_times))
plt.xlim((0, max_frames))
plt.savefig('theta_diff.png')
print('done plotting')