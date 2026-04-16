import pandas as pd

import torch
import torch.nn as nn


# # Set the device to use
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# print("Device -> ", device)

# # Define the hyperparameters
# num_features = 3
# input_size = num_features
# hidden_size = 66
# output_size = num_features
learning_rate = 0.001
# rounds = 1000
epochs = 40
# torch_seed = 0

# rows_per_partition = 3600  #1 hour (3600 seconds) per user
# num_user_regs = 5          #Number of regs (location and orientation) received by round
# num_user_regs_per_time = 1 #1 reg with location and orientation by second
# accuracy_threshold = 99.5  #Model accuracy threshold


def startModel(filename='edge_cloud_result.csv'):
    df = pd.read_csv(filename)

    features = [feature for feature in df.columns if feature != 'qoe']

    print(f"Features: {features}")

    num_layers = 3
    num_features = len(features)

    model = LSTMModel(num_features, 66, num_layers, num_features)
    model.trainModel(df[features].values, df['qoe'].values)

    return model


class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super(LSTMModel, self).__init__()
        self.num_layers  = num_layers
        self.hidden_size = hidden_size
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        # Initialize hidden state
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size).to(device)

        # Forward pass
        out, _ = self.lstm(x, (h0, c0))

        # Use the output at the last time step
        out = self.fc(out[:, -1, :])

        return out

    
    def trainModel(self, X_train, y_train):
        pass
    
    def predict(self, X_test):
        # Make predictions
        with torch.no_grad():
            inputs = torch.from_numpy(X_test).float().to(device)
            return self(inputs).cpu().numpy()
        
    def saveModel(self, filename):
        # Save the model
        torch.save(self.state_dict(), filename) 

    def loadModel(self, filename):
        # Load the model
        self.load_state_dict(torch.load(filename))
        self.eval()
