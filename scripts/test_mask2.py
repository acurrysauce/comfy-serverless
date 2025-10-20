import numpy as np
from PIL import Image

# Create a test mask centered at y=1024 (the grass-stone boundary)
width, height = 2048, 2048
mask = np.zeros((height, width), dtype=np.uint8)

# White stripe from y=704 to y=1344 (640px wide, centered at y=1024)
mask[704:1344, :] = 255

Image.fromarray(mask, mode='L').save('test_centered_mask.png')
print("Created test mask: white stripe from y=704 to y=1344 (centered at boundary)")
