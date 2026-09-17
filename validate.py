import numpy as np

'''
Validations of data integrity
'''

def cloudFilter(image, cloud_threshold=0.10, shadow_threshold=0.3):

    '''
    Calculates cloud and shadow percentages
    Validates if pass by thresholds
    '''
    
    # float to avoid caculus(ingles ruim) error
    img_float = image.astype(float)
    pixels_totais = img_float[0].size
    
    # rgb mean to get bright
    bright = np.mean(img_float, axis=0)

    # calculates brightness        
    px_cloud = np.count_nonzero(bright > 200) 
    px_shadow = np.count_nonzero(bright < 10) 
    
    # percentage
    cloud_pct = (px_cloud / pixels_totais)
    shadow_pct = (px_shadow / pixels_totais)
    
    # thresholds
    if cloud_pct > cloud_threshold or shadow_pct > shadow_threshold:        
        return False
    
    else:
        return True


def dataIntegrity(image, threshold=0.10):
    '''
    Verify data integrity
    Images with no data
    '''

    total_pixels = image[0].size
    empty_pixels = np.count_nonzero(image[0] == 0)
    
    if (empty_pixels / total_pixels) > 0.10:
        return False
    else:
        return True