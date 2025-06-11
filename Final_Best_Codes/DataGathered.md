Dataset Data 
9 emotions 
angry - 
boring - 
disgust -
fear -
happy -
neutral - 
sad -
stress -
suprised - 


## Mobile Net
size - 256
Epoch - 13
Train Loss: 0.2946
Val Accuracy - 60.99%


## YOLO11
with earlt stopping
size - 256
Epoch - 100

cls_loss (Classification Loss)
Definition: Measures how well the model classifies the object within the detected box.
Meaning: If you're detecting emotions or object types, this measures the error in those predictions.


box_loss (Bounding Box Loss)
Definition: Measures the error in predicted bounding box coordinates vs the ground truth.
Used in: Detection models only (not classification or segmentation).
Meaning: Lower is better. Indicates how well the model is predicting the locations of objects.

dfl_loss (Distribution Focal Loss)
Definition: A specialized loss for bounding box regression using a discrete probability distribution over locations.
Meaning: Helps the model more accurately estimate bounding box borders with high precision.