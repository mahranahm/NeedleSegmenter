from nipype.interfaces.fsl import PRELUDE
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import cv2
from skimage.filters import meijering, frangi, sato
from scipy import ndimage

slice = 2

magn_file = ('full/raw/85.nii')
phase_file = ('full/raw/86.nii')

phase = nib.load(phase_file)
phase_numpy = phase.get_fdata()
paffine = phase.affine

rad = (phase_numpy*3.14159)/4096

ss = nib.Nifti1Image(rad, paffine)
nib.save(ss, 'full/radphase.nii')

img = nib.load(magn_file)
nii_numpy = img.get_fdata()
affine = img.affine

ret,mask = cv2.threshold(nii_numpy,70,100,cv2.THRESH_BINARY)
# mask = nii_numpy > 55
mask1 = np.array(mask)
mask1 = mask1.astype(int)

ss = nib.Nifti1Image(mask1, affine)
nib.save(ss, 'full/mask.nii')

#FSL PRELUDE : PHASE UNWRAPPED
pre = PRELUDE()
pre.inputs.phase_file = r"full/radphase.nii"
pre.inputs.magnitude_file = (magn_file)
pre.inputs.mask_file = r"full/mask.nii"
pre.run()

# GAUSSIAN HIGH FILTER

uphase = nib.load(r'radphase_unwrapped.nii.gz')
uphase_numpy = uphase.get_fdata()
uphaseaffine = uphase.affine

uphase_numpy = uphase_numpy[:,:,slice]

I = uphase_numpy
A = np.fft.fft2(I)
A1 = np.fft.fftshift(A)

#Image size
[M, N] = A.shape

#filter size parameter
R = 10

X = np.arange(0, N, 1)
Y = np.arange(0, M, 1)
# Y = Y.astype(int)

[X,Y] = np.meshgrid(X,Y)
Cx = 0.5*N
Cy = 0.5*M
Lo = np.exp(-(((X - Cx)**2) + ((Y - Cy)**2)) / ((2 * R)**2))
Hi = 1 - Lo

J = A1 * Lo
J1 = np.fft.ifftshift(J)
B1 = np.fft.ifft2(J1)

K = A1 * Hi
K1 = np.fft.ifftshift(K)
B2 = np.fft.ifft2(K1)
B2 = np.real(B2)

mask5 = nib.load(r'full/mask.nii')
mask6 = mask5.get_fdata()
mask6 = mask6[:,:,slice]


# border widths; 
border_size = 20
top, bottom, left, right = [border_size]*4
mask6 = cv2.copyMakeBorder(mask6, top, bottom, left, right, cv2.BORDER_CONSTANT, (0,0,0))


#kernel1 = np.ones((3,3),np.uint8)
# mask3 = cv2.morphologyEx(mask6, cv2.MORPH_CLOSE, kernel1)

kernel = np.ones((5,5),np.uint8)
mask3 = cv2.erode(mask6,kernel,iterations=2)
mask3 = ndimage.binary_fill_holes(mask3).astype(np.uint8)

x, y = mask3.shape
mask4 = mask3[0+border_size:y-border_size, 0+border_size:x-border_size]

B2 = cv2.bitwise_and(B2,B2, mask=mask4)


meiji = meijering(B2, sigmas=(1,1), black_ridges=True)

#meiji = cv2.GaussianBlur(meiji, (3,3), 0)

(minVal, maxVal, minLoc, maxLoc) = cv2.minMaxLoc(meiji)

result2 = np.reshape(meiji, meiji.shape[0]*meiji.shape[1])

# sort = np.flip(np.argsort(result2))
# sort = (np.argpartition(result2, -1)[-11:])
ids = np.argpartition(result2, -51)[-51:]
sort = ids[np.argsort(result2[ids])[::-1]]



print (sort[0],sort[1],sort[2],sort[3],sort[4],sort[5],sort[6])

(y1, x1) = np.unravel_index(sort[4], meiji.shape) # best match

point = (x1,y1)
circle1 = plt.Circle(point,2,color='red')

nii_numpy = nii_numpy[:,:,slice]

fig, axs = plt.subplots(1,2)
fig.suptitle('Needle Tracking')
axs[0].imshow(nii_numpy, cmap='gray')
axs[0].set_title('Magnitude + Tracked')
axs[0].add_artist(circle1)
axs[0].axis('off')
axs[1].set_title('Processed Phase Image')
axs[1].imshow(meiji, cmap='hsv')
axs[1].axis('off')
plt.show()


