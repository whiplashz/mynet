import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.utils.data as td
import time
import torch.optim as optim
from torchvision import datasets, transforms


device = 'cuda' if torch.cuda.is_available() else 'cpu'


class FCNet(nn.Module):
    def __init__(self):
        super(FCNet, self).__init__()
        self.fc = nn.Linear(in_features=28 * 28,
                            out_features=10)

    def forward(self, x):
        x = torch.flatten(x, start_dim=1)
        x = self.fc(x)
        output = F.log_softmax(x, dim=1)
        return output


class SimpleCNN(nn.Module):
    def __init__(self):
        super(SimpleCNN, self).__init__()
        self.conv = nn.Conv2d(in_channels=1,
                              out_channels=10,
                              kernel_size=3,
                              stride=2,
                              padding=1)
        self.fc = nn.Linear(in_features=28 * 28 * 10 // (2 * 2),
                            out_features=10)

    def forward(self, x):
        x = self.conv(x)
        x = F.relu(x)
        x = torch.flatten(x, start_dim=1)
        x = self.fc(x)
        output = F.log_softmax(x, dim=1)
        return output

image_width = 28
image_height = 28
image_channels = 1
n_classes = 10

kernel_size = 3
conv1_filters = 8
conv2_filters = 16
linear2 = 100

massive_dropout = 0.2
ligth_dropout = 0.1

linear1 = (image_width * image_height) // (4 ** 2) * conv2_filters

class MyNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.sequential = nn.Sequential(
            nn.Conv2d(image_channels, conv1_filters, kernel_size, padding='same', bias=False),
            nn.BatchNorm2d(conv1_filters),
            nn.MaxPool2d(2),
            nn.ReLU(),

            nn.Dropout(ligth_dropout),
            nn.Conv2d(conv1_filters, conv2_filters, kernel_size, padding='same', bias=False),
            nn.BatchNorm2d(conv2_filters),
            nn.MaxPool2d(2),
            nn.ReLU(),

            nn.Flatten(start_dim=1),
            nn.Dropout(massive_dropout),
            nn.Linear(linear1, linear2),
            nn.BatchNorm1d(linear2),
            nn.ReLU(),

            nn.Dropout(ligth_dropout),
            nn.Linear(linear2, n_classes),
            nn.BatchNorm1d(n_classes),

            nn.LogSoftmax(dim=1)
        )

    def forward(self, X):
        return self.sequential(X)

def get_model_class(_):
    """ Do not change, needed for AE """
    return [MyNet]


def classify(model, x):
    return torch.argmax(model(x), dim=1)


def accuracy(pred, y):
    return pred.eq(y).sum().item() / len(y)


def error(pred, y):
    return pred.ne(y).sum().item() / len(y)


def load_model(model):
    model.load_state_dict(torch.load('model.pt'))

def train(model: nn.Module):
    batch_sz = 64

    learning_rate = 1
    epochs = 20

    dataset = datasets.FashionMNIST('data', train=True, download=True,
                                    transform=transforms.ToTensor())

    trn_size = int(0.09 * len(dataset))
    val_size = int(0.01 * len(dataset))
    add_size = len(dataset) - trn_size - val_size  # you don't need ADDitional dataset to pass

    trn_dataset, val_dataset, add_dataset = torch.utils.data.random_split(dataset, [trn_size,
                                                                                    val_size,
                                                                                    add_size])
    trn_loader = torch.utils.data.DataLoader(trn_dataset,
                                             batch_size=batch_sz,
                                             shuffle=True)

    val_loader = torch.utils.data.DataLoader(val_dataset,
                                             batch_size=batch_sz,
                                             shuffle=False)

    device = torch.device("cpu")
    model = model.to(device)

    optimizer = optim.SGD(model.parameters(), lr=learning_rate)

    for epoch in range(1, epochs + 1):
        # training
        model.train()
        for i_batch, (x, y) in enumerate(trn_loader):
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            net_output = model(x)
            loss = F.nll_loss(net_output, y)
            loss.backward()
            optimizer.step()

            if i_batch % 100 == 0:
                print('[TRN] Train epoch: {}, batch: {}\tLoss: {:.4f}'.format(
                    epoch, i_batch, loss.item()))

        # validation
        model.eval()
        correct = 0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                net_output = model(x)

                prediction = classify(model, x)
                correct += prediction.eq(y).sum().item()
        val_accuracy = correct / len(val_loader.dataset)
        print('[VAL] Validation accuracy: {:.2f}%'.format(100 * val_accuracy))

        torch.save(model.state_dict(), "model.pt")


if __name__ == '__main__':
    train(SimpleCNN())
