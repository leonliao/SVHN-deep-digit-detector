#-*- coding: utf-8 -*-
import object_detector.file_io as file_io
import object_detector.factory as factory
import cv2
import numpy as np
import pickle

np.set_printoptions(linewidth = 1000, suppress = True)

CONFIGURATION_FILE = "conf/new_format.json"

import object_detector.utils as utils

# Todo : extractor module 에 내용과 중복된다. 리팩토링하자.
def get_truth_bb(image_file, annotation_path):
    image_id = utils.get_file_id(image_file)
    annotation_file = "{}/annotation_{}.mat".format(annotation_path, image_id)
    bb = file_io.FileMat().read(annotation_file)["box_coord"][0]
    return bb

# intersection of union
def calc_iou(boxes, truth_box):
    y1 = boxes[:, 0]
    y2 = boxes[:, 1]
    x1 = boxes[:, 2]
    x2 = boxes[:, 3]
    
    y1_gt = truth_box[0]
    y2_gt = truth_box[1]
    x1_gt = truth_box[2]
    x2_gt = truth_box[3]
    
    xx1 = np.maximum(x1, x1_gt)
    yy1 = np.maximum(y1, y1_gt)
    xx2 = np.minimum(x2, x2_gt)
    yy2 = np.minimum(y2, y2_gt)

    w = np.maximum(0, xx2 - xx1 + 1)
    h = np.maximum(0, yy2 - yy1 + 1)
    
    intersections = w*h
    As = (x2 - x1 + 1) * (y2 - y1 + 1)
    B = (x2_gt - x1_gt + 1) * (y2_gt - y1_gt + 1)
    
    ious = intersections.astype(float) / (As + B -intersections)
    return ious


def calc_precision_recall(probs, ground_truths):
    probs = np.array(probs)
    ground_truths = np.array(ground_truths)
    
    dataset = np.concatenate([probs.reshape(-1,1), ground_truths.reshape(-1,1)], axis=1)
    dataset = dataset[dataset[:, 0].argsort()[::-1]]
    
    # print dataset
    
    n_gts = len(dataset[dataset[:, 1] == 1])
    n_relevant = 0.0
    n_searched = 0.0
    
    recall_precision = []
    
    for data in dataset:
        n_searched += 1
        if data[1] == 1:
            n_relevant += 1
        recall = n_relevant / n_gts
        precision = n_relevant / n_searched
        recall_precision.append((recall, precision))
        
        if recall == 1.0:
            break
    
    return np.array(recall_precision)

def calc_interpolated_precision(recall_precision, desired_recall):
    inter_precision = recall_precision[recall_precision[:,0] >= desired_recall]
    inter_precision = inter_precision[:, 1]
    inter_precision = max(inter_precision)
    return inter_precision

def calc_average_precision(recall_precision):
    # calc interpolated precision
    
    inter_precisions = []
    for i in range(11):
        recall = float(i) / 10
        inter_precisions.append(calc_interpolated_precision(recall_precision, recall))
        
    return np.array(inter_precisions).mean()
    

if __name__ == "__main__":
    
    # 1. Load configuration file and test images
    conf = file_io.FileJson().read(CONFIGURATION_FILE)
    test_image_files = file_io.list_files(conf["dataset"]["pos_data_dir"], n_files_to_sample=2)

    # 2. Build detector and save it   
    detector = factory.Factory.create_detector(conf["descriptor"]["algorithm"], conf["descriptor"]["parameters"],
                                               conf["classifier"]["algorithm"], conf["classifier"]["parameters"], conf["classifier"]["output_file"])
    patches = []
    probs = []
    gts = []
      
    # 3. Run detector on Test images 
    for image_file in test_image_files:
        test_image = cv2.imread(image_file)
        test_image = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
             
        print "[INFO] Test Image shape: {0}".format(test_image.shape)
       
        boxes, probs_ = detector.run(test_image, 
                                    conf["detector"]["window_dim"], 
                                    conf["detector"]["window_step"], 
                                    conf["detector"]["pyramid_scale"], 
                                    threshold_prob=0.0)
          
        # Test Image �� ���� Ground-Truth �� Read
        truth_bb = get_truth_bb(image_file, conf["dataset"]['annotations_dir'])
        ious = calc_iou(boxes, truth_bb)
        is_positive = ious > 0.5
        # detector.show_boxes(test_image, boxes)
         
        patches += boxes.tolist()
        probs += probs_.tolist()
        gts += is_positive.tolist()

    # Test Code           
    probs.append(0.8)
    gts.append(0)
    probs = np.array(probs)
    gts = np.array(gts)

    recall_precision = calc_precision_recall(probs, gts)
    print calc_average_precision(recall_precision)
    
#     [INFO] Test Image shape: (197L, 300L)
#     [INFO] Test Image shape: (197L, 300L)
#     0.848484848485

    

    
    
    

    
    
    
    
    
    
    
    
    
    
    
    
        




