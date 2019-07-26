import h5py
import numpy as np
import pandas as pd
import os
import imageio
from scipy import ndimage

def get_grains_from_h5(h5_dir, file_name):
    '''
    Function that reads in h5 and returns numpy arrays
    '''
    f = h5py.File(os.path.join(h5_dir,file_name), 'r')
    DCT_grains = f['LabDCT']['Data']['GrainId'][()] #get values from HDF5
    DCT_colours = f['LabDCT']['Data']['IPF001'][()]
    DCT_Rodrigues = f['LabDCT']['Data']['Rodrigues'][()]
    print(' GrainId Max: {}\n GrainId Min: {}\n Shape: {}\n'.format(
    DCT_grains.max(), DCT_grains.min(), DCT_grains.shape))
    print(' Rodrigues Max: {}\n Rodrigues Min: {}\n Shape: {}\n'.format(
    DCT_Rodrigues.max(), DCT_Rodrigues.min(), DCT_Rodrigues.shape))
    return DCT_grains, DCT_colours, DCT_Rodrigues


def get_grain_location(data, grain_id):
    '''
    Function that returns index values of locations for a given grainId value
    '''
    locations = np.asarray(np.where(data == grain_id))

    return locations


def indexing_func(key_list, value_list):
    '''
    Function that creates a greyscale image of lookup values for all unique colours in image stack
    '''
    key_map = {tuple(key): i for i, key in enumerate(key_list)}
    result = np.array([key_map[tuple(value)] for value in value_list])
    return result

def fill_grains(GrainIds, GrainX):
    avg_x_med = np.zeros_like(GrainX)
    for grain_id in range(GrainIds.max()+1):
        grain = get_grain_location(GrainIds, grain_id)
        avg_x = GrainX[tuple(grain)].mean(axis=0)
        avg_x_med[tuple(grain)] = avg_x
    return avg_x_med

def colour_indexing(GrainColours):
    flattened_imgs = GrainColours.reshape((-1,3))
    colours = np.unique(flattened_imgs, axis=0)
    indexed_imgs = indexing_func(colours, flattened_imgs)
    indexed_imgs = indexed_imgs.reshape((GrainColours.shape[0:3]))
    return indexed_imgs, colours

def saving_tif(path, dir_name, stack, np_array=None):

    try:
        os.mkdir(os.path.join(path, dir_name))
        print("Directory " , dir_name ,  " Created ")
    except FileExistsError:
        print("Directory " , dir_name ,  " already exists")

    for i in range(len(stack)):
        imageio.imwrite(os.path.join(path, dir_name,'indexed'+str(i)+'.tif'),
            stack[i,:,:].astype(np.uint16))
    if np_array is not None:
        np.save(os.path.join(path,'DCTcolours.npy'), np_array)


def main():
    h5_dir = r'\\xrm\Files\AppsDemo2\X-ray_Systems\Louisiana State University'
    file_name = 'LSU_DCT.h5'
    GrainIds, GrainColours, GrainRod = get_grains_from_h5(h5_dir, file_name)
    # Apply median filter to grain id, use this boundary as what to fill colours
    GrainIds = ndimage.median_filter(GrainIds, 7)
    GrainColours = fill_grains(GrainIds, GrainColours)
    GrainRod = fill_grains(GrainIds, GrainRod)
    GrainColoursIndexed, colours = colour_indexing(GrainColours)
    saving_tif(h5_dir, 'Indexed', GrainColoursIndexed, colours)



if __name__ == '__main__':
    main()
