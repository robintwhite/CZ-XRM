import h5py
import numpy as np
import pandas as pd
import os
import imageio
from scipy import ndimage
import time
import datetime

##TODO: get pixel spacing and offsets from data in h5

def get_spacing(h5_dir, file_name, ts):
    '''
    Function that reads in h5 and creates text file of info
    '''
    f = h5py.File(os.path.join(h5_dir,file_name), 'r')
    Abs_pixel = pd.Series(f['AbsorptionCT']['Spacing'][()], name='Absorption px')
    DCT_pixel = pd.Series(f['LabDCT']['Spacing'][()], name='DCT px') #get values from HDF5
    frame = {'Absorption px (mm)': Abs_pixel, 'DCT px (mm)': DCT_pixel}
    df = pd.DataFrame(frame)
    print(df)
    df.to_csv(os.path.join(h5_dir,'header{}.txt'.format(ts)), header=True, index=None, sep=',', mode='w')


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

def get_abs_data_and_save_tif(ts, h5_dir, file_name):
    f = h5py.File(os.path.join(h5_dir,file_name), 'r')
    dir_name = 'AbsorptionCT_tifs'+ts
    try:
        Abs = f['AbsorptionCT']['Data'][()] #get values from HDF5
    except KeyError:
        print('No absorption data found')

    try:
        os.mkdir(os.path.join(h5_dir, dir_name))
        print("Directory " , dir_name ,  " Created ")
    except FileExistsError:
        print("Directory " , dir_name ,  " already exists")

    for i in range(len(Abs)):
        imageio.imwrite(os.path.join(h5_dir, dir_name,'Abs'+str(i)+'.tif'),
            Abs[i,:,:].astype(np.uint16))

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

def saving_coloured_tif(ts, path, dir_name, stack, np_array=None):
    dir_name = dir_name+ts
    try:
        os.mkdir(os.path.join(path, dir_name))
        print("Directory " , dir_name ,  " Created ")
    except FileExistsError:
        print("Directory " , dir_name ,  " already exists")

    for i in range(len(stack)):
        imageio.imwrite(os.path.join(path, dir_name,'indexed'+str(i)+'.tif'),
            stack[i,:,:].astype(np.uint16))
    if np_array is not None:
        np.save(os.path.join(path,'DCTcolours{}.npy'.format(ts)), np_array)


def main():

    ts = time.time()
    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H%M%S')

    h5_dir = r'D:\Graz'
    file_name = 'Tu_Graz_DCT.h5'

    get_spacing(h5_dir, file_name, st)
    # GrainIds, GrainColours, GrainRod = get_grains_from_h5(h5_dir, file_name)
    # # Apply median filter to grain id, use this boundary as what to fill colours
    # GrainIds = ndimage.median_filter(GrainIds, 7)
    # GrainColours = fill_grains(GrainIds, GrainColours)
    # GrainRod = fill_grains(GrainIds, GrainRod)
    # GrainColoursIndexed, colours = colour_indexing(GrainColours)
    # saving_coloured_tif(st, h5_dir, 'Indexed', GrainColoursIndexed, colours)
    # get_abs_data_and_save_tif(st, h5_dir, file_name)



if __name__ == '__main__':
    main()
