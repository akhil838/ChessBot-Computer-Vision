# ChessBot-Computer-Vision
Model Capable of Detecting chess pieces, and augmenting the next move in realtime !

## Dataset
![Screen Recording 2025-04-14 at 7 27 02 PM](https://github.com/user-attachments/assets/68c2516a-9657-421c-85f4-5930e8d171e1)</br>
* The model is completely trained on synthetic data generated using blender
* Each Chess Piece is Crafted using the existing real-life piece taken as a reference
* The blend file also includes the python script to automate the making of dataset
    * Randomize camera and lighting positions
    * place chess pieces according to FEN
    * Capture image and Save annotations

## Inference
![WhatsApp Video 2025-04-21 at 21 15 35](https://github.com/user-attachments/assets/21f4d158-887c-4532-9758-553a5962fc13)


## Installation

Follow the steps below to set up and run the project.

### 1. Clone the repository

```bash
git clone https://github.com/akhil838/ChessBot-Computer-Vision.git
cd ChessBot-Computer-Vision
```

2. (Optional) Create and activate a virtual environment

```
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install required Python packages
```
pip install -r requirements.txt
```
4. Install PyTorch
If you have a CUDA-compatible GPU

Visit the official PyTorch installation guide and install the appropriate version based on your CUDA version. Example for CUDA 12.1:
```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
If you are using CPU only
```
pip install torch torchvision torchaudio
```
Running the Program

Start the Jupyter notebook:
```
jupyter notebook run.ipynb
```
