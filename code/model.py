#!/usr/bin/env python

import torch.nn as nn


class Autoencoder3D(nn.Module):

    def __init__(self):
        super(Autoencoder3D, self).__init__()

        # Architecture adopted from:
        #  https://www.sciencedirect.com/science/article/pii/S1361841517301287

        # Create memoryless-blocks for reuse
        self.relu = nn.ReLU(True)
        self.sigm = nn.Sigmoid()

        ########
        #
        #  Encoder layers:
        #
        ########

        # Layer input image size: 1x48x56x48 ; Kernel size: 1
        # N channels in: 1 ; N channels out: 32 ; Stride: 1
        # Layer output image size: 32x48x56x48 ; Pad: 0
        self.conv1 = nn.Conv3d(1, 32, kernel_size=1, padding=0)

        # Layer input image size: 32x48x56x48 ; Kernel size: 2
        # N channels in: 32 ; N channels out: 32 ; Stride: 1
        # Layer output image size: 32x24x28x24 ; Pad: 0
        self.pool1 = nn.MaxPool3d(2, return_indices=True)

        # Layer input image size: 32x24x28x24 ; Kernel size: 5
        # N channels in: 32 ; N channels out: 32 ; Stride: 1
        # Layer output image size: 32x24x28x24 ; Pad: 2
        self.conv2 = nn.Conv3d(32, 32, kernel_size=5, padding=2)

        # Layer input image size: 32x48x56x48 ; Kernel size: 2
        # N channels in: 32 ; N channels out: 32 ; Stride: 1
        # Layer output image size: 32x12x14x12 ; Pad: 0
        self.pool2 = nn.MaxPool3d(2, return_indices=True)

        # Layer input image size: 32x12x14x12 ; Kernel size: 5
        # N channels in: 32 ; N channels out: 32 ;  Stride: 1
        # Layer output image size: 32x12x14x12 ; Pad: 2
        self.conv3 = nn.Conv3d(32, 32, kernel_size=5, padding=2)

        # Layer input image size: 32x12x14x12 ; Kernel size: 2
        # N channels_in: 32 ; N channels_out: 32 ;  Stride: 1
        # Layer output image size: 32x6x7x6
        self.pool3 = nn.MaxPool3d(2, return_indices=True)

        # Layer input image size: 32x6x7x6 ; Kernel size: 1
        # N channels in: 32 ; N channels out: 1 ;  Stride: 1
        # Layer output image size: 1x6x7x6 ; Pad: 0
        self.conv4 = nn.Conv3d(32, 1, kernel_size=1, padding=0)

        ########
        #
        #  Decoder layers:
        #
        ########

        # Layer input image size: 1x6x7x6 ; Kernel size: 1
        # N channels in: 1 ; N channels out: 1 ;  Stride: 1
        # Layer output image size: 1x6x7x6 ; Pad: 0
        self.deconv4 = nn.ConvTranspose3d(1, 1, kernel_size=1, padding=0)

        # Layer input image size: 1x6x7x6 ; Kernel size: 2
        # N channels in: 1 ; N channels out: 1 ;  Stride: 2
        # Layer output image size: 1x12x14x12 ; Pad: 0
        #self.unpool3 = nn.MaxUnpool3d(2, stride=2)
        # N.B. Cannot use MaxUnpool3d here because this pooling was done with 32
        # filters and unpooling is attempted with 1 filter.
        # TODO: consider this implication on all other unpooling steps.
        self.unpool3 = nn.Upsample(scale_factor=2)

        # Layer input image size: 1x12x14x12 ; Kernel size: 5
        # N channels in: 1 ; N channels out: 32 ;  Stride: 1
        # Layer output image size: 32x12x14x12 ; Pad: 2
        self.deconv3 = nn.ConvTranspose3d(1, 32, kernel_size=5, padding=2)

        # Layer input image size: 32x12x14x12 ; Kernel size: 2
        # N channels in: 32 ; N channels out: 32 ;  Stride: 2
        # Layer output image size: 32x24x28x24 ; Pad: 0
        self.unpool2 = nn.MaxUnpool3d(2, stride=2)

        # Layer input image size: 32x24x28x24 ; Kernel size: 5
        # N channels in: 32 ; N channels out: 32 ;  Stride: 1
        # Layer output image size: 32x24x28x24 ; Pad: 2
        self.deconv2 = nn.ConvTranspose3d(32, 32, kernel_size=5, padding=2)

        # Layer input image size: 32x24x28x24 ; Kernel size: 2
        # N channels in: 32 ; N channels out: 32 ;  Stride: 2
        # Layer output image size: 32x48x56x48 ; Pad: 0
        self.unpool1 = nn.MaxUnpool3d(2, stride=2)

        # Layer input image size: 32x48x56x48 ; Kernel size: 1
        # N channels in: 32 ; N channels out: 1 ;  Stride: 1
        # Layer output image size: 1x48x56x48 ; Pad: 0
        self.deconv1 = nn.ConvTranspose3d(32, 1, kernel_size=1, padding=0)

    ########
    #
    #  Constructed Encoder
    #
    ########
    def encoder(self, x):
        x = self.conv1(x)
        x = self.relu(x)
        x, ind1 = self.pool1(x)
        x = self.conv2(x)
        x = self.relu(x)
        x, ind2 = self.pool2(x)
        x = self.conv3(x)
        x = self.relu(x)
        x, ind3 = self.pool3(x)
        x = self.conv4(x)
        x = self.relu(x)
        return x, [ind1, ind2, ind3]

    ########
    #
    #  Constructed Decoder
    #
    ########
    def decoder(self, x, indices):
        ind1, ind2, ind3 = indices
        x = self.deconv4(x)
        x = self.relu(x)
        # x = self.unpool3(x, ind3)  # TODO: see note on :76
        x = self.unpool3(x)
        x = self.deconv3(x)
        x = self.relu(x)
        x = self.unpool2(x, ind2)
        x = self.deconv2(x)
        x = self.relu(x)
        x = self.unpool1(x, ind1)
        x = self.deconv1(x)
        x = self.relu(x)
        x = self.sigm(x)
        return x

    ########
    #
    #  Forward Propagation
    #
    ########
    def forward(self, x):
        x, indices = self.encoder(x)
        x = self.decoder(x, indices)
        return x
