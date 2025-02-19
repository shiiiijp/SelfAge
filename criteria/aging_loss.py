import torch
from torch import nn
import torch.nn.functional as F

from models.dex_vgg import VGG

model_paths = {'age_predictor': 'pretrained_model/dex_age_classifier.pth'}

class AgingLoss(nn.Module):

    def __init__(self):
        super(AgingLoss, self).__init__()
        self.age_net = VGG()
        ckpt = torch.load(model_paths['age_predictor'], map_location="cpu")['state_dict']
        ckpt = {k.replace('-', '_'): v for k, v in ckpt.items()}
        self.age_net.load_state_dict(ckpt)
        self.age_net.cuda()
        self.age_net.eval()
        self.min_age = 0
        self.max_age = 100

    def __get_predicted_age(self, age_pb):
        predict_age_pb = F.softmax(age_pb)
        predict_age = torch.zeros(age_pb.size(0)).type_as(predict_age_pb)
        for i in range(age_pb.size(0)):
            for j in range(age_pb.size(1)):
                predict_age[i] += j * predict_age_pb[i][j]
        return predict_age

    def extract_ages(self, x):
        x = F.interpolate(x, size=(224, 224), mode='bilinear')
        predict_age_pb = self.age_net(x)['fc8']
        predicted_age = self.__get_predicted_age(predict_age_pb)
        return predicted_age

    def forward(self, y_hat, target_ages):
        output_ages = self.extract_ages(y_hat) / 100.

        loss = F.mse_loss(output_ages, target_ages)
        return loss, output_ages
