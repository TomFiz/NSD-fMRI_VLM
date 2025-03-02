import os
import csv
import torch
import numpy as np
from torch import nn
from PIL import Image
from pathlib import Path
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms
# from lavis.processors.randaugment import RandomAugment
from torchvision.transforms.functional import InterpolationMode
device = 'cuda'
torch.manual_seed(5)

class MRI_dataset(Dataset):
    def __init__(self, subj, data_type, brain_type, vis_transform, txt_transform, data_dir, csv_file_path):
        self.subj = format(subj, '02')
        self.data_dir = os.path.join(data_dir, 'subj'+self.subj)
        self.brain_type = brain_type
        self.normalize = transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        self.vis_transform = vis_transform
        # transforms.Compose(
        #     [
        #         transforms.RandomResizedCrop(
        #             224,
        #             scale=(0.5, 1),
        #             interpolation=InterpolationMode.BICUBIC,
        #         ),
        #         transforms.RandomHorizontalFlip(),
        #         RandomAugment(
        #             2,
        #             5,
        #             isPIL=True,
        #             augs=[
        #                 "Identity",
        #                 "AutoContrast",
        #                 "Brightness",
        #                 "Sharpness",
        #                 "Equalize",
        #                 "ShearX",
        #                 "ShearY",
        #                 "TranslateX",
        #                 "TranslateY",
        #                 "Rotate",
        #             ],
        #         ),
        #         transforms.ToTensor(),
        #         self.normalize,
        #     ]
        # )
        self.txt_transform = txt_transform

        if data_type == 'train':
            self.img_dir = os.path.join(self.data_dir, 'training_split', 'training_images')
            self.fmri_dir = os.path.join(self.data_dir, 'training_split', 'training_fmri')
            self.csv_file_path = os.path.join(csv_file_path,'subj' + self.subj, 'subj' +self.subj + '_train.csv')

        if data_type == 'test':
            self.img_dir = os.path.join(self.data_dir, 'test_split', 'test_images')
            self.csv_file_path = os.path.join(csv_file_path,'subj' + self.subj, 'subj' +self.subj + '_test.csv')
        
        self.imgs_paths = sorted(list(Path(self.img_dir).iterdir()))
        self.mri_array = self.read_fMRI_data()
        self.image_list = self.read_image_list()
        self.text_dict = self.read_text_csv_file()

        self.mri_dim = self.mri_array.shape[-1]

    def read_image_list(self):
        img_list = os.listdir(self.img_dir)
        img_list.sort()
        return img_list
    
    def read_fMRI_data(self):
        if self.brain_type == 'left':
            lh_fmri = np.load(os.path.join(self.fmri_dir, 'lh_training_fmri.npy'))
            return lh_fmri
        if self.brain_type == 'right':
            rh_fmri = np.load(os.path.join(self.fmri_dir, 'rh_training_fmri.npy'))
            return rh_fmri
    
    def read_text_csv_file(self):
        text_dict = {}
        with open(self.csv_file_path,'r') as data:
            for line in csv.reader(data):
                text_dict[line[0]] = line[1]
        return text_dict

    def __len__(self):
        return len(self.image_list)

    def __getitem__(self, idx):

        img_path = self.imgs_paths[idx]
        img_name = str(img_path).split("/")[-1].replace('.png', '')

        img = Image.open(img_path).convert('RGB')

        img = self.vis_transform["eval"](img).to(device)

        mri = self.mri_array[idx]
        
        caption = self.text_dict[img_name]
        sen = self.txt_transform["eval"](caption)

        return img, sen, mri



class MRI_test_dataset(Dataset):
    def __init__(self, subj, data_type, brain_type, vis_transform, txt_transform, data_dir, csv_file_path):
        self.subj = format(subj, '02')
        self.data_dir = os.path.join(data_dir, 'subj'+self.subj)
        self.brain_type = brain_type
        self.normalize = transforms.Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711))
        # self.vis_transform = transforms.Compose(
        #     [
        #         transforms.RandomResizedCrop(
        #             224,
        #             scale=(0.5, 1),
        #             interpolation=InterpolationMode.BICUBIC,
        #         ),
        #         transforms.RandomHorizontalFlip(),
        #         RandomAugment(
        #             2,
        #             5,
        #             isPIL=True,
        #             augs=[
        #                 "Identity",
        #                 "AutoContrast",
        #                 "Brightness",
        #                 "Sharpness",
        #                 "Equalize",
        #                 "ShearX",
        #                 "ShearY",
        #                 "TranslateX",
        #                 "TranslateY",
        #                 "Rotate",
        #             ],
        #         ),
        #         transforms.ToTensor(),
        #         self.normalize,
        #     ]
        # )
        self.txt_transform = txt_transform

        if data_type == 'train':
            self.img_dir = os.path.join(self.data_dir, 'training_split', 'training_images')
            self.fmri_dir = os.path.join(self.data_dir, 'training_split', 'training_fmri')
            self.csv_file_path = os.path.join(csv_file_path,'subj' + self.subj, 'subj' +self.subj + '_train.csv')

        if data_type == 'test':
            self.img_dir = os.path.join(self.data_dir, 'test_split', 'test_images')
            self.fmri_dir = os.path.join(self.data_dir, 'training_split', 'training_fmri')
            self.csv_file_path = os.path.join(csv_file_path,'subj' + self.subj, 'subj' +self.subj + '_test.csv')
        
        self.imgs_paths = sorted(list(Path(self.img_dir).iterdir()))
        self.image_list = self.read_image_list()
        self.text_dict = self.read_text_csv_file()

        self.mri_array = self.read_fMRI_data()
        self.mri_dim = self.mri_array.shape[-1]

    def read_image_list(self):
        img_list = os.listdir(self.img_dir)
        img_list.sort()
        return img_list
    
    def read_fMRI_data(self):
        if self.brain_type == 'left':
            lh_fmri = np.load(os.path.join(self.fmri_dir, 'lh_training_fmri.npy'))
            return lh_fmri
        if self.brain_type == 'right':
            rh_fmri = np.load(os.path.join(self.fmri_dir, 'rh_training_fmri.npy'))
            return rh_fmri
    
    def read_text_csv_file(self):
        text_dict = {}
        with open(self.csv_file_path,'r') as data:
            for line in csv.reader(data):
                text_dict[line[0]] = line[1]
        return text_dict

    def __len__(self):
        return len(self.image_list)
    
    def __getitem__(self, idx):

        img_path = self.imgs_paths[idx]
        img_name = str(img_path).split("/")[-1].replace('.png', '')

        img = Image.open(img_path).convert('RGB')

        img = self.vis_transform(img).to(device)
        
        caption = self.text_dict[img_name]
        sen = self.txt_transform["eval"](caption)

        return img, sen

def train_test_split(train_dataset, batch_size, shuffle=False):
    train_size = int(0.9 * len(train_dataset))
    eval_size = int(0.08 * len(train_dataset))
    test_size = len(train_dataset) - train_size - eval_size

    train_data, eval_data, test_data = random_split(train_dataset, [train_size,eval_size, test_size])
    #train_data = torch.utils.data.ConcatDataset([train_data, eval_data])

    train_loader = DataLoader(train_data, batch_size=batch_size, shuffle=shuffle)
    eval_loader = DataLoader(eval_data, batch_size=batch_size, shuffle=shuffle)
    test_loader = DataLoader(test_data, batch_size=batch_size, shuffle=shuffle)

    return train_loader, eval_loader, test_loader

class noisy_celing_metric:
    def __init__(self, data_dir, subj, brain_type):
        self.subj = format(subj, '2')
        self.data_dir = os.path.join(data_dir,'subject_nc')
        self.noisy_celing_path = os.path.join(self.data_dir, 'subject'+ self.subj.strip() +'_' + brain_type + '_' + 'nc.npy')
        self.nc_array = None
    
    def load_nc_file(self):
        nc_array = np.load(self.noisy_celing_path)
        return nc_array
    
    def calculate_metric(self, mri_correlation):
        self.nc_array = self.load_nc_file()

        self.nc_array[self.nc_array==0] = 1e-14
        mri_correlation[mri_correlation<0] = 0

        mri_correlation = mri_correlation ** 2
        mri_correlation = mri_correlation.to('cpu')

        cor_array = mri_correlation / self.nc_array
        mask =  ~torch.isinf(cor_array)
        cor_array = cor_array[mask]

        cor_array[cor_array > 1] = 1

        corr = torch.median(cor_array)

        return corr * 100