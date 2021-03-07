# Data Pre-processing for ICIAR 2018 Challenge

[ICIAR 2018 Grand Challenge on Breast Cancer Histology images](https://iciar2018-challenge.grand-challenge.org/) provides [data](https://iciar2018-challenge.grand-challenge.org/Dataset/) in form of `.svs` and the corresponding `.xml` annotation files. 

The `main.py` script cut the whole slide image into patches based on the region of interest. (Because a large region of the whole slide images are considered normal and thus are not relevant for performance evaluation.)


## Environment
- Python 3.6.8.
- OpenSlide


## Usage

```python
# Install requirements
pip install -r requirements.txt

# Run the main script
python main.py
```


## Results
After runing the main script, results of image patches will be generated in `splited_svs`, `splited_xml`, `splited_svs_little`, `splited_xml_little`, `splited_xml_little_P` and `splited_svs_resize`, inside the `data/` folder.
- **splited_svs**: 5000 x 5000 RGB images.
- **splited_xml**: 5000 x 5000 RGB mask of interest.
- **splited_svs_little**: 1000 x 1000 RGB images cropped from splited_svs.
- **splited_xml_little**: 1000 x 1000 RGB images cropped from splited_xml.
- **splited_xml_little_P**: Gray sclae version of 1000 x 1000 RGB images cropped from splited_xml, annotate type as the pixel value.
- **splited_svs_resize**: Resized 500 x 500 RGB images patches of splited_svs.


`Original .svs whole slide image preview`
<p align="center">
<img width="600" src="https://github.com/12vv/ICIAR2018DataPreprocessing/blob/master/images/svs_preview.png">
</p>

`splited_svs and splited_xml samples`
<p align="center">
<img width="600" src="https://github.com/12vv/ICIAR2018DataPreprocessing/blob/master/images/1.png">
</p>

`splited_svs_little and splited_xml_little samples`
<p align="center">
<img width="600" src="https://github.com/12vv/ICIAR2018DataPreprocessing/blob/master/images/2.png">
</p>



## Acknowledgments
The script `xml_to_mask.py` is borrowed from [brendonlutnick/extract_xml_region](https://github.com/brendonlutnick/extract_xml_region), and the whole project is inspired by it.



