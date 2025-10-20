import numpy as np
from PIL import Image

# Create a test mask to see where it's applied
width, height = 2048, 2048
mask = np.zeros((height, width), dtype=np.uint8)

# Top 512px: black (preserve)
# Middle 1024px: white (inpaint) - this should be at the grass-stone boundary
# Bottom 512px: black (preserve)
mask[512:1536, :] = 255

Image.fromarray(mask, mode='L').save('test_horizontal_mask.png')
print("Created test mask: white stripe from y=512 to y=1536")
