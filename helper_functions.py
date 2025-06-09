from shapely.geometry import Polygon, Point
import subprocess
from PIL import ImageFont, ImageDraw, Image
import platform
import cv2
import numpy as np
import warnings
warnings.filterwarnings("ignore")


def get_available_cameras():
    available_cameras = []
    # Check for 5 cameras
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            available_cameras.append(i)
            cap.release()
    return available_cameras

def draw_perspective_grid(image, corners, grid_size=8, color=(0, 0, 255), thickness=1, dev_mode=True):
    """
    Draws an 8x8 grid inside a quadrilateral defined by `corners` using perspective transform.

    Params:
    - image: original image (BGR)
    - corners: list of 4 (x, y) tuples, approx corners of a square
    - grid_size: number of divisions along each side (default 8)
    - color: line color for drawing
    - thickness: thickness of the grid lines
    """
    img = image.copy()
    h, w = image.shape[:2]
    square_size = 800  # working warped image size

    # Sort corners: top-left, top-right, bottom-right, bottom-left
    def sort_corners(pts):
        pts = np.array(pts, dtype=np.float32)
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        return np.array([
            pts[np.argmin(s)],      # top-left
            pts[np.argmin(diff)],   # top-right
            pts[np.argmax(s)],      # bottom-right
            pts[np.argmax(diff)]    # bottom-left
        ], dtype=np.float32)

    src = sort_corners(corners)
    dst = np.array([
        [0, 0],
        [square_size, 0],
        [square_size, square_size],
        [0, square_size]
    ], dtype=np.float32)

    # Perspective transform matrices
    M = cv2.getPerspectiveTransform(src, dst)
    M_inv = cv2.getPerspectiveTransform(dst, src)

    step = square_size // grid_size

    intersection_points = []

    # Compute all intersections in warped space
    for i in range(grid_size + 1):
        intersection_points.append([])
        for j in range(grid_size + 1):
            pt = np.array([[[j * step, i * step]]], dtype=np.float32)
            pt_orig = cv2.perspectiveTransform(pt, M_inv)[0][0]
            pt_orig_int = tuple(np.int32(pt_orig))
            cv2.drawMarker(image, pt_orig_int, (0, 255, 255), thickness=2)
            intersection_points[-1].append(pt_orig_int)

    if dev_mode:
        # Draw vertical lines in warped space, then inverse transform
        for i in range(1, grid_size):
            x = i * step
            pt1 = np.array([[[x, 0]]], dtype=np.float32)
            pt2 = np.array([[[x, square_size]]], dtype=np.float32)
            pt1_orig = cv2.perspectiveTransform(pt1, M_inv)[0][0]
            pt2_orig = cv2.perspectiveTransform(pt2, M_inv)[0][0]
            cv2.line(img,
                     tuple(np.int32(pt1_orig)),
                     tuple(np.int32(pt2_orig)),
                     color, thickness)

        # Draw horizontal lines in warped space, then inverse transform
        for i in range(1, grid_size):
            y = i * step
            pt1 = np.array([[[0, y]]], dtype=np.float32)
            pt2 = np.array([[[square_size, y]]], dtype=np.float32)
            pt1_orig = cv2.perspectiveTransform(pt1, M_inv)[0][0]
            pt2_orig = cv2.perspectiveTransform(pt2, M_inv)[0][0]
            cv2.line(img,
                     tuple(np.int32(pt1_orig)),
                     tuple(np.int32(pt2_orig)),
                     color, thickness)

        # Optionally draw outer border
        cv2.polylines(img, [np.int32(src)], isClosed=True, color=(255, 0, 0), thickness=2)

    warped = cv2.warpPerspective(img, M, (square_size, square_size))
    warped = cv2.resize(warped, (300, 300))
    cv2.imshow('warped', warped)

    return img, intersection_points

def get_perspective_piece(coords, corners):
    def sort_corners(pts):
        pts = np.array(pts, dtype=np.float32)
        s = pts.sum(axis=1)
        diff = np.diff(pts, axis=1)
        return np.array([
            pts[np.argmin(s)],      # top-left
            pts[np.argmin(diff)],   # top-right
            pts[np.argmax(s)],      # bottom-right
            pts[np.argmax(diff)]    # bottom-left
        ], dtype=np.float32)

    square_size = 800  # working warped image size
    src = sort_corners(corners)
    dst = np.array([
        [0, 0],
        [square_size, 0],
        [square_size, square_size],
        [0, square_size]
    ], dtype=np.float32)

    # Perspective transform matrices
    M = cv2.getPerspectiveTransform(src, dst)
    M_inv = cv2.getPerspectiveTransform(dst, src)

    x1, y1, x2, y2 = coords
    piece_centre = np.array([[[(x1 + x2) / 2 ,y2]]],dtype=np.float32)
    #print(piece_centre)
    piece_corner_transformed = cv2.perspectiveTransform(piece_centre, M)[0][0]
    #print(piece_corner_transformed)

    piece_corner_transformed[1] -= 10
    return cv2.perspectiveTransform(np.array([[piece_corner_transformed]],dtype= np.float32), M_inv)[0][0]

def check_any_bbox_overlap(bboxes):
    """
    Checks if any of the 4 bounding boxes overlap.

    Args:
        bboxes (list of tuple): List of 4 bounding boxes in (x_min, y_min, x_max, y_max) format.

    Returns:
        bool: True if any two boxes overlap, else False.
    """
    def boxes_overlap(box1, box2):
        x1_min, y1_min, x1_max, y1_max = box1
        x2_min, y2_min, x2_max, y2_max = box2

        # Check if there is no overlap
        if x1_max <= x2_min or x2_max <= x1_min:
            return False
        if y1_max <= y2_min or y2_max <= y1_min:
            return False

        return True

    # Check all pairs
    for i in range(len(bboxes)):
        for j in range(i + 1, len(bboxes)):
            if boxes_overlap(bboxes[i], bboxes[j]):
                return True

    return False

def get_board(intersection_points, perspective_pieces):
    board = []
    FEN_label = {
    "Pawn_w": "P", "Knight_w": "N", "Bishop_w": "B", "Rook_w": 'R', "Queen_w": 'Q', "King_w": 'K',
    "Pawn_b": "p", "Knight_b": "n", "Bishop_b": 'b', "Rook_b": 'r', "Queen_b": 'q', "King_b": 'k',
    }
    try:
        #print(intersection_points)
        for i in range(8):
            row = ''
            #empty_count = 0
            for j in range(8):
                top_left = Point(intersection_points[i][j])
                top_right = Point(intersection_points[i][j+1])
                bottom_right = Point(intersection_points[i+1][j])
                bottom_left = Point(intersection_points[i+1][j+1])
                #print(i,j,top_left, top_right, bottom_right, bottom_left)
                polygon = Polygon([top_left, top_right, bottom_right, bottom_left])
                for corner,label in perspective_pieces:
                    if polygon.contains(Point(corner)):
                        #print(label)
                        # if empty_count:
                        #     row += str(empty_count)
                        #     empty_count = 0
                        row += FEN_label[label]
                        break
                else:
                    row += '.'
                    #empty_count += 1
                #print(j)
            #print(i,row)
            board.append(row)

    except Exception as e:
        print(e)
        board = None
    return board

def start_stockfish(path):
    # Example usage
    # Replace 'stockfish' with the path to your Stockfish executable if it's not in your system's PATH
    engine = subprocess.Popen(
        [path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1
    )

    # Example: Send the 'uci' command to initialize UCI mode
    engine.stdin.write('uci\n')
    engine.stdin.flush()

    # Read and print the engine's response
    while True:
        output = engine.stdout.readline()
        if output.strip() == 'uciok':
            print('Stockfish Initialized')
            break

    return engine

def stockfish_nextmove(engine, fen):
    # Set the position using the provided FEN
    engine.stdin.write(f'position fen {fen}\n')
    engine.stdin.flush()

    # Instruct Stockfish to search for the best move within a time limit (e.g., 1 second)
    engine.stdin.write('go movetime 500\n')
    engine.stdin.flush()

    best_move = None
    # Read lines until the best move is found
    empty_line_count = 0
    while True:
        line = engine.stdout.readline()
        if line == '':
            empty_line_count += 1

        if line.startswith('bestmove'):
            best_move = line.split()[1]
            break

        if empty_line_count > 100:
            best_move = None
            break

    # Terminate the Stockfish process


    return best_move

def augument_nextMove(frame, next_move,inx_points):
    image = frame.copy()
    init_coords = 8 - (int(next_move[1])-1), (ord(next_move[0])-97)
    #init_coords= 1,1
    final_coords = 8 - (int(next_move[3])-1), (ord(next_move[2])-97)
    #print(init_coords, final_coords)
    init_box = np.array([[
        inx_points[init_coords[0]][init_coords[1]],
        inx_points[init_coords[0]-1][init_coords[1]],
        inx_points[init_coords[0]-1][init_coords[1]+1],
        inx_points[init_coords[0]][init_coords[1]+1]
        ]],dtype= np.int32)#.reshape(-1,1,2)
    final_box = np.array([[
        inx_points[final_coords[0]][final_coords[1]],
        inx_points[final_coords[0]-1][final_coords[1]],
        inx_points[final_coords[0]-1][final_coords[1]+1],
        inx_points[final_coords[0]][final_coords[1]+1]
    ]],dtype= np.int32)#.reshape(-1,1,2)
    frame = cv2.fillPoly(frame, init_box, (255,255,255))
    frame = cv2.fillPoly(frame, final_box, (0,0,255))
    alpha = 0.5
    frame = cv2.addWeighted(frame, alpha, image, 1 - alpha, 0, image)

    return frame

def find_unicode_font():
    system = platform.system()
    if system == "Windows":
        return "C:/Windows/Fonts/seguisym.ttf"
    elif system == "Darwin":
        return "/System/Library/Fonts/Supplemental/Arial Unicode.ttf"
    elif system == "Linux":
        return "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    else:
        raise RuntimeError("Unsupported OS for font detection.")

def display_chess_fen(fen: str):
    piece_unicode = {
        'P': '♙', 'N': '♘', 'B': '♗', 'R': '♖', 'Q': '♕', 'K': '♔',
        'p': '♟', 'n': '♞', 'b': '♝', 'r': '♜', 'q': '♛', 'k': '♚',
    }

    board_size = 480
    square_size = board_size // 8
    light_square = (239, 239, 209)  # From uploaded image
    dark_square = (120, 140, 82)    # From uploaded image

    img = np.ones((board_size, board_size, 3), dtype=np.uint8) * 255
    img_pil = Image.fromarray(img)
    draw = ImageDraw.Draw(img_pil)

    font_path = find_unicode_font()
    font = ImageFont.truetype(font_path, square_size - 10)

    position = fen.split()[0]
    rows = position.split('/')

    for row_idx in range(8):
        for col_idx in range(8):
            x = col_idx * square_size
            y = row_idx * square_size
            color = light_square if (row_idx + col_idx) % 2 == 0 else dark_square
            draw.rectangle([x, y, x + square_size, y + square_size], fill=color)

    for row_idx, row in enumerate(rows):
        col_idx = 0
        for char in row:
            if char.isdigit():
                col_idx += int(char)
            else:
                piece = piece_unicode.get(char)
                if piece:
                    x = col_idx * square_size
                    y = row_idx * square_size
                    bbox = font.getbbox(piece)
                    w = bbox[2] - bbox[0]
                    h = bbox[3] - bbox[1]
                    draw.text(
                        (x + (square_size - w) / 2, y + (square_size - h) / 2 - 5),
                        piece,
                        font=font,
                        fill=(0, 0, 0)
                    )
                col_idx += 1

    img = np.array(img_pil)
    cv2.imshow("FEN Chess Board", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


