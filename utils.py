import numpy as np 
import json
import cv2
import os 

class ImageAnnotation():
    def get_corner_coordinates(self, image_path):
        '''
        NOTE: 
        - REMEMBER TO POINT IN THIS ORDER (TOPLEFT->TOPRIGHT->BOTLEFT->BOTRIGHT)
        - AFTER CHOOSING 4 POINTS, PRESS "ENTER" TO DRAW BOUNDING BOXES
        '''
        corner_coordinates = []
        small_width = 350
        def click_event(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                corner_coordinates.append([x, y])
                # print(f'Point: ({x}, {y})')
                cv2.circle(img, (x, y), 3, (0, 0, 255), -1)
                cv2.imshow('Find Out Corner Coordinate', img)
                if len(corner_coordinates) == 4:
                    show_small_image()

        def show_small_image():
            if len(corner_coordinates) == 4:
                warped_image = self.warp(image_path, corner_coordinates)
                small_img = cv2.resize(warped_image, (small_width, int(small_width * 35 / 65)))
                img[0:small_img.shape[0], 0:small_width] = small_img
            cv2.imshow('Find Out Corner Coordinate', img)

        def redraw_points():
            # Redraw all points
            temp_img = original_img.copy()
            for point in corner_coordinates:
                cv2.circle(temp_img, tuple(point), 3, (0, 0, 255), -1)
            if len(corner_coordinates) < 4:
                # Clear the small image area if fewer than 4 points
                temp_img[img.shape[0]-int(small_width * 35 / 65):img.shape[0], 0:small_width] = original_img[img.shape[0]-int(small_width * 35 / 65):img.shape[0], 0:small_width]
            cv2.imshow('Find Out Corner Coordinate', temp_img)
            return temp_img

        img = cv2.imread(image_path)
        original_img = img.copy()
        if img is None:
            print("Error: Image not found.")
            return None

        cv2.namedWindow('Find Out Corner Coordinate')
        cv2.setMouseCallback('Find Out Corner Coordinate', click_event)
        cv2.imshow('Find Out Corner Coordinate', img)

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == 13: # click ENTER
                break
            elif key == ord('r') and corner_coordinates:
                corner_coordinates.pop()  # Remove the last point
                img = redraw_points()  # Redraw the image without the last point

        cv2.destroyAllWindows()
        return corner_coordinates

    def warp(self, image_path, corner_coordinates):
        img = cv2.imread(image_path)
        input_points = np.float32(corner_coordinates)
        output_w, output_h = 650, 350

        converted_points = np.float32([[0, 0], [output_w, 0], [0, output_h], [output_w, output_h]])

        matrix = cv2.getPerspectiveTransform(input_points, converted_points)
        warped_img = cv2.warpPerspective(img, matrix, (output_w, output_h))

        return warped_img
    
    def binariez(self, warped_img):
        gray_img = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
        blurred_img = cv2.GaussianBlur(gray_img, (5, 5), 0)
        _, binary_img = cv2.threshold(blurred_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return binary_img
    
    def interact_with_image(self, image):
        '''
        NOTE: DRAW BOUNDING BOX IN THIS ORDER:
        1. UPPER TO LOWER FOR CELL
        2. LEFT TO RIGHT FOR DIGITs
        3. START FROM TOPLEFT, END AT BOTRIGHT FOR EACH BOUNDING BOX
        4. PRESS "ENTER" TO FINISH
        '''
        refPt = []  # List to store the starting and ending points of rectangles
        rectangles = []  # List to store coordinates of all rectangles drawn
        is_cropping = False  # Boolean flag indicating if cropping (drawing) is in process
        clone = image.copy()  # Create a copy of the image
        bbox_list = []

        def click_and_crop(event, x, y, flags, param):
            nonlocal refPt, is_cropping, image
            # if the left mouse button was clicked, record the starting
            # (x, y) coordinates and indicate that cropping is being performed
            if event == cv2.EVENT_LBUTTONDOWN:
                refPt = [(x, y)]
                is_cropping = True

            # check to see if the left mouse button was released
            elif event == cv2.EVENT_LBUTTONUP:
                refPt.append((x, y))
                is_cropping = False

                # Draw bbox
                cv2.rectangle(image, refPt[0], refPt[1], (0, 255, 0), 1)
                cv2.imshow("image", image)

                # Add rectangle to draw
                rectangles.append((refPt[0], refPt[1]))

                x_start, y_start = refPt[0]
                x_end, y_end = refPt[1]
                width = abs(x_end - x_start)
                height = abs(y_end - y_start)
                # print(f"Bounding Box: (x={x_start}, y={y_start}, w={width}, h={height})")

                # Add bbox
                bbox_list.append([x_start, y_start, width, height])

        cv2.namedWindow("image")
        cv2.setMouseCallback("image", click_and_crop)

        while True:
            cv2.imshow("image", image)
            key = cv2.waitKey(1) & 0xFF

            if key == ord("r"):
                if rectangles:
                    rectangles.pop()
                    bbox_list.pop()
                    image = clone.copy()
                    for rect in rectangles:
                        cv2.rectangle(image, rect[0], rect[1], (0, 255, 0), 1)
                    cv2.imshow("image", image)

            elif key == 13:
                break
        
        cv2.destroyAllWindows()
        return bbox_list if len(bbox_list) != 0 else []
    
    def save_annotation(self, warp_coordinates, bbox_list, json_path):
        price_boxes = bbox_list[:6]
        liters_boxes = bbox_list[6:]

        # bbox saved in format [x, y, w, h]
        data = {
            "warp" : warp_coordinates,
            "price": price_boxes,
            "liters": liters_boxes
        }
        print(data)
        if all(lst for lst in [warp_coordinates, price_boxes, liters_boxes]):
            if not os.path.exists(json_path):
                with open(json_path, 'w') as f:
                    json.dump(data, f, indent=4)
                print(f"Saved coordinates at {json_path} successfully.")
            else:
                print(f"File {json_path} already exists. Maybe you already annotate this pump")
        else:
            print('At least 1 of these things is empty: warp, price or liter')

    
    def extract_and_save_digits(self, cv2_image, pump_json, save_path):
        with open(pump_json, 'r') as file:
            data = json.load(file)
            keys = data.keys()
            
            for key in keys:
                if key == 'price' or key == 'liter':                    
                    cell = data[key]
                    for i, (x, y, w, h) in enumerate(cell):
                        new_save_path = save_path[:-4] + "_" + str(i) + save_path[-4:]
                        region = cv2_image[y:y+h, x:x+w]
                        if cv2.sumElems(region)[0] != 0:
                            cv2.imwrite(new_save_path, region)
        print(f'Saved images in {new_save_path} successfully')

    
    def execute(self, image_path, json_path, save_path):
        corner_coordinates = self.get_corner_coordinates(image_path)   
        warped_img = self.warp(image_path, corner_coordinates)
        # binary_img = self.binariez(warped_img)
        # binary_img_for_draw_bbox = cv2.cvtColor(binary_img, cv2.COLOR_GRAY2BGR) # convert back to BGR to show color bounding box
        bbox_list = self.interact_with_image(warped_img)

        self.save_annotation(corner_coordinates, bbox_list, json_path)
        self.extract_and_save_digits(warped_img, json_path, save_path)
        
    def cut_only(self, image_path, json_path, save_path):
        with open(json_path, 'r') as file:
            data = json.load(file)
            corner_coordinates = data['warp']
            warped_img = self.warp(image_path, corner_coordinates)
            # binary_img = self.binariez(warped_img)
            self.extract_and_save_digits(warped_img, json_path, save_path)