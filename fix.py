import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from transformers import BertTokenizer, BertModel
import torch
import re, json
import torch.nn as nn
from torch.utils.data import DataLoader, SubsetRandomSampler, TensorDataset
from sklearn.model_selection import KFold
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from torch.utils.data import DataLoader, random_split, TensorDataset
from torch.optim import Adam, Adamax
import torch.nn.functional as F
import random

class TextCNN(nn.Module):
    def __init__(self, embed_dim, num_classes, num_filters, filter_sizes, dropout=0.2):
        super(TextCNN, self).__init__()
        self.convs = nn.ModuleList([
            nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=k) for k in filter_sizes
        ])
        self.dropout = nn.Dropout(dropout)
        self.fc1 = nn.Linear(num_filters * len(filter_sizes), 64)
        self.fc2 = nn.Linear(64, num_classes)

    def forward(self, x):
        x = x.permute(0, 2, 1)
        x = [F.relu(conv(x)) for conv in self.convs]
        x = [F.max_pool1d(i, i.size(2)).squeeze(2) for i in x]
        x = torch.cat(x, 1)
        x = self.dropout(x)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)

# Fungsi untuk membersihkan teks dan mengganti singkatan
def prepro(text):
    # Dictionary untuk memetakan singkatan ke bentuk panjangnya
    singkatan_ke_panjang = {
        'ti': 'teknik industri',
        'te': 'teknik elektro',
        'tsd': 'teknologi sains data',
        'rn': 'rekayasa nanoteknologi',
        'trkb': 'teknik Robotika dan kecerdasan buatan',
        'ftmm': 'fakultas teknologi maju dan multidisiplin',
        'fttm': 'fakultas teknologi maju dan multidisiplin',
        'stmm': 'fakultas teknologi maju dan multidisiplin',
        'ukt': 'uang kuliah tunggal',
        'lab': 'laboratorium',
        'medsos': 'media sosial',
        'spp': 'sumbangan pembinaan pendidikan',
        'bem': 'badan eksekutif mahasiswa',
        'blm': 'badan legislatif mahasiswa',
        'ormawa': 'organisasi mahasiswa'
        # Tambahkan lebih banyak sesuai kebutuhan
    }
    # Lowercasing
    text = text.lower()
    # Mengganti singkatan dengan bentuk panjangnya dalam teks
    for abbrev, full_form in singkatan_ke_panjang.items():
        text = re.sub(r'\b' + abbrev + r'\b', full_form, text, flags=re.IGNORECASE)
    # Remove unnecessary characters
    text = re.sub(r'[^a-z0-9\s]', '', text)
    return text

tokenizer = BertTokenizer.from_pretrained('indobenchmark/indobert-base-p2')
model = BertModel.from_pretrained('indobenchmark/indobert-base-p2')

# inisialisasi model
# Parameter sesuai spesifikasi
embedding_dim = 768  # Ukuran dari setiap embedding
output_dim = 27  # Jumlah output classes
num_filters = 32  # Jumlah neuron pada Conv1D
filter_sizes = [3,4,5]  # Ukuran filter
dropout_rate = 0.2  # Dropout rate
device = torch.device('cpu')
final_model = TextCNN(embed_dim=embedding_dim, num_classes=output_dim, num_filters=num_filters, filter_sizes=filter_sizes, dropout=dropout_rate).to(device)
final_model.load_state_dict(torch.load("2904_FinalCNNmodel_Fold 4.pth", map_location = torch.device('cpu')))
final_model.eval()

def wordembed(text):
    # Initialize the tokenizer and model
    global tokenizer, model
    encoded_input = tokenizer(text,
                                add_special_tokens=True,
                                max_length=29,
                                return_tensors='pt',
                                return_attention_mask=True,
                                padding='max_length')
    input_ids = encoded_input['input_ids']
    attention_masks = encoded_input['attention_mask']
    with torch.no_grad():
        # outputs = model(**encoded_input)
        outputs = model(input_ids, attention_mask=attention_masks)
        embeddings = outputs.last_hidden_state
    return embeddings

label_path = "label_mapping.json"
# Muat label mapping dari file JSON
with open(label_path, 'r') as f:
    label_mapping = json.load(f)

# Decode predicted label
def decode_label(encoded_label):
    global label_mapping
    if isinstance(encoded_label, torch.Tensor):
        encoded_label = encoded_label.item()  # Konversi tensor ke int
    return label_mapping[str(encoded_label)]  # Konversi int ke str untuk mencocokkan dengan kunci JSON
with open('new_data.json', 'r', encoding='utf-8') as json_data:
        intents = json.load(json_data)
        
def get_response(teks):
    global intents, final_model   
    teks_input = teks
    teks_prepro = prepro(teks_input)
    teks_embbed = wordembed(teks_prepro)
    predictions = final_model(teks_embbed)

    # Dapatkan confidence dan prediksi
    probabilities = F.softmax(predictions, dim=1)
    max_confidence, predicted_label = torch.max(probabilities, dim=1)
    confidence_percent = max_confidence.item() * 100  # Konversi ke persentase
    response = decode_label(predicted_label)
    if confidence_percent > 90:
        for intent in intents['intents']:
            if response == intent["tag"]:
                return random.choice(intent['responses']), response
    else:
        return "Maaf, saya tidak cukup yakin untuk menjawab pertanyaan tersebut. Mohon hubungi admin kami +62XXXXXXXXXXXXXX", "Undefined"
