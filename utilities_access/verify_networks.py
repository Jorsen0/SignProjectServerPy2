# Siamese-Networks

import torch
import torch.nn as nn
import torch.nn.functional as F

# CNN: input len -> output len
# Lout=floor((Lin+2∗padding−dilation∗(kernel_size−1)−1)/stride+1)

LEARNING_RATE = 0.0005
WEIGHT_DECAY = 0.0000002
EPOCH = 500
BATCH_SIZE = 64

class SiameseNetwork(nn.Module):
    def __init__(self, train=True):
        nn.Module.__init__(self)
        if train:
            self.status = 'train'
        else:
            self.status = 'eval'

        self.cnn1 = nn.Sequential(
            nn.Conv1d(  # 14 x 128
                in_channels=14,
                out_channels=28,
                kernel_size=8,
                padding=4,
                stride=4,
            ),
            nn.ReLU(),
            # todo need Norm ? yes
            nn.BatchNorm1d(28),  # 28 x 32
            # todo need pooling ? yes
            nn.MaxPool1d(kernel_size=2),  # 28 x 16

            nn.Conv1d(
                in_channels=28,
                out_channels=32,
                kernel_size=4,
                padding=2,
                stride=1
            ),
            nn.ReLU(),
            nn.BatchNorm1d(32),  # 32 x 32
            nn.MaxPool1d(kernel_size=2),  # 32 x 10
        )

        self.out = nn.Sequential(
            # nn.Linear(32 * 34 , 128), 没有池化层 输出长度是34
            nn.Linear(32 * 8, 128),
            nn.ReLU(),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, 32)
        )

    def forward_once(self, x):
        x = self.cnn1(x)
        x = x.view(x.size(0), -1)
        out = self.out(x)
        return out

    def forward(self, *xs):
        if self.status == 'train':
            out1 = self.forward_once(xs[0])
            out2 = self.forward_once(xs[1])
            return out1, out2
        else:
            return self.forward_once(xs[0])

class ContrastiveLoss(torch.nn.Module):
    """
    Contrastive loss function.
    Based on: http://yann.lecun.com/exdb/publis/pdf/hadsell-chopra-lecun-06.pdf
    """

    def __init__(self, margin=2.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin

    def forward(self, output1, output2, label):
        euclidean_distance = F.pairwise_distance(output1, output2)
        loss_contrastive = torch.mean((1 - label) * torch.pow(euclidean_distance, 2) +
                                      label * torch.pow(torch.clamp(self.margin - euclidean_distance,
                                                                    min=0.0), 2))
        return loss_contrastive
