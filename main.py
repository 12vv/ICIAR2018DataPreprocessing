import numpy as np
import os
import cv2
import openslide
import lxml.etree as ET
import matplotlib.pyplot as plt
from glob import glob
from skimage.io import imsave, imread
from skimage.transform import resize
from PIL import Image
from xml_to_mask import xml_to_mask
from PIL import Image

# cwd = os.getcwd() # default: in the directory that contain this script
cwd = 'WSI/'  # change to dataset directory (contains corresponding .svs and .xml)
save_dir = 'data'

save_splited_svs = save_dir + '/splited_svs/'  # need to create the folders first
save_mask_dir = save_dir + '/splited_xml/'    # need to create the folders first
save_splited_svs_little = save_dir + '/splited_svs_little/'
save_mask_dir_little = save_dir + '/splited_xml_little/'    # need to create the folders first
save_mask_dir_little_P = save_dir + '/splited_xml_little_P/'    # need to create the folders first
resize_dir = save_dir + '/splited_svs_resize/'

size_thresh = None # not saved is uder this px area
final_image_size = 5000 # final_image_size
white_background = False # mask the structure
extract_one_region = True # include only one structure per patch (ignore other structures in ROI)

WSIs_ = glob(cwd + '/*.svs')
print("Total WSIs:", len(WSIs_))
WSIs = []
XMLs = []

for WSI in WSIs_:
    xml_ = glob(WSI.split('.')[0] + '.xml')
    if xml_ != []:
        print('including: ' + WSI)
        XMLs.append(xml_[0])
        WSIs.append(WSI)

def create_splited():
    # go though all WSI
    for idx, XML in enumerate(XMLs):
        bounds, masks = get_annotation_bounds(XML,1)
        basename = os.path.basename(XML)
        basename = os.path.splitext(basename)[0]

        print('opening: ' + WSIs[idx])
        pas_img = openslide.OpenSlide(WSIs[idx])

        for idxx, bound in enumerate(bounds):
            if extract_one_region:
                mask = masks[idxx]
            else:
                mask=(xml_to_mask(XML,(bound[0],bound[1]), (final_image_size,final_image_size), downsample_factor=1, verbose=0))

            if size_thresh == None:
                PAS = pas_img.read_region((int(bound[0]),int(bound[1])), 0, (final_image_size,final_image_size))
                PAS = np.array(PAS)[:,:,0:3]

            else:
                size=np.sum(mask)
                if size >= size_thresh:
                    PAS = pas_img.read_region((bound[0],bound[1]), 0, (final_image_size,final_image_size))
                    PAS = np.array(PAS)[:,:,0:3]

            if white_background:
                for channel in range(3):
                    PAS_ = PAS[:,:,channel]
                    PAS_[mask == 0] = 255
                    PAS[:,:,channel] = PAS_

            subdir = '{}/{}/'.format(save_splited_svs,basename)
            # make_folder(subdir)
            imsave(save_splited_svs + basename + '_' + str(idxx) + '_image.png', PAS)


def get_annotation_bounds(xml_path, annotationID=1):
    # parse xml and get root
    tree = ET.parse(xml_path)
    root = tree.getroot()

    Regions = root.findall("./Annotation[@Id='" + str(annotationID) + "']/Regions/Region")

    bounds = []
    masks = []

    i = 0
    for Region in Regions:
        # Benign, Invasive carcinoma, In situ carcinoma
        type = Region.attrib.get('Text')
        # type = Region.findall("./Attributes/Attribute")[0].attrib['Value']   # only for A01
        # print(type)

        Vertices = Region.findall("./Vertices/Vertex")
        x = []
        y = []

        for Vertex in Vertices:
            x.append(int(np.float32(Vertex.attrib['X'])))
            y.append(int(np.float32(Vertex.attrib['Y'])))

        x_center = min(x) + ((max(x)-min(x))/2)
        y_center = min(y) + ((max(y)-min(y))/2)

        bound_x = x_center-final_image_size/2
        bound_y = y_center-final_image_size/2
        bounds.append([bound_x, bound_y])

        points = np.stack([np.asarray(x), np.asarray(y)], axis=1)
        points[:, 1] = np.int32(np.round(points[:,1] - bound_y ))
        points[:, 0] = np.int32(np.round(points[:,0] - bound_x ))
        mask = np.zeros([final_image_size, final_image_size], dtype=np.uint8)

        rgb_mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)

        if type == 'Benign':
            color = [0, 255, 0]
        elif type == 'Invasive carcinoma':
            color = [0, 0, 255]
        else:
            color = [255, 0, 0]

        cv2.fillPoly(rgb_mask, [points], color)

        file_name = xml_path.split('/')[-1].split('.')[0] + '_' + str(i) + '_anno.png'
        i = i+1

        cv2.imwrite(save_mask_dir + file_name, rgb_mask)
        # print(save_mask_dir + file_name)

        # plt.imshow(mask)
        # plt.show()
        masks.append(mask)

    return bounds, masks

def make_folder(directory):
    if not os.path.exists(directory):
        os.makedirs(directory) # make directory if it does not exit already # make new directory


def make_txt(base_path, store_file):
    with open(store_file, 'w', encoding='utf-8') as f:
        for filename in os.listdir(base_path):
            f.write(filename)
            f.write('\n')


def crop(infile,height,width):
    im = Image.open(infile)
    imgwidth, imgheight = im.size
    for i in range(imgheight//height):
        for j in range(imgwidth//width):
            box = (j*width, i*height, (j+1)*width, (i+1)*height)
            yield im.crop(box)

# After creating splited_svs and splited_xml (5000x5000),
# now create splited_svs_little and splited_xml_little (1000x1000)
def create_splited_little(splited_dir, save_path, height, width):
    PNGs = glob(splited_dir + '/*.png')
    for png in PNGs:
        num = 0
        file_name = png.split('/')[-1]
        file_name_pre = file_name.split('.')[0]
        crop_path = splited_dir + file_name
        print("croping:", crop_path)
        for k, piece in enumerate(crop(crop_path, height, width), num):
            img = Image.new('RGB', (height, width), 255)
            img.paste(piece)

            img_copy = Image.new('L', (height, width), 0)
            pixels = img.load()
            for i in range(img_copy.size[0]):  # for every pixel:
                for j in range(img_copy.size[1]):
                    # set the colour accordingly
                    if pixels[i, j] == (0, 0, 0):
                        img_copy.putpixel((i, j), (0))
                    elif pixels[i, j] == (0, 0, 255):
                        # pixels[i, j] = (1, 1, 1)
                        img_copy.putpixel((i, j), (1))
                    elif pixels[i, j] == (255, 0, 0):
                        # pixels[i, j] = (2, 2, 2)
                        img_copy.putpixel((i, j), (2))
                    elif pixels[i, j] == (0, 255, 0):
                        # pixels[i, j] = (3, 3, 3)
                        img_copy.putpixel((i, j), (3))

            path = save_path + file_name_pre + "_%s.png" % k
            # path_P = save_mask_dir_little_P + file_name_pre + "_%s.png" % k
            # path = os.path.join('save_path', "file_name", "_%s.png" % k)
            # print("save to:", path)
            img.save(path)
            # img_copy.save(path_P)


# make splited_svs_resize
# resize files in splited_svs
def make_resize():
    # save_splited_svs
    PNGs = glob(save_splited_svs + '/*.png')
    for png in PNGs:
        file_name = png.split('/')[-1]
        img = Image.open(png)
        resize_img = img.resize((500, 500))
        path = resize_dir + file_name
        resize_img.save(path)


if __name__ == '__main__':
    # create_splited()
    # print("splited (5000x5000) complete!")
    create_splited_little(save_splited_svs, save_splited_svs_little, 1000, 1000)
    print("splited_svs_little (1000x1000) complete!")
    create_splited_little(save_mask_dir, save_mask_dir_little, 1000, 1000)  # save_mask_dir_little
    print("splited_xml_little (1000x1000) complete!")

    # write into txt
    make_txt(save_mask_dir_little, 'train.txt')
    print("data/train.txt complete!")

    # make resize
    make_resize()
    print("splited_svs_resize (500x500) complete!")
