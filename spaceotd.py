#!/usr/bin/env python3
import pygame
from sys import exit
import requests
from datetime import datetime, timedelta
from PIL import Image
from io import BytesIO


'''
INSTRUCTIONS
 - Make sure you have pygame installed.
    - 'pip3 install pygame'
 - In same directory create a file called api.txt
 - Register an api key at https://api.nasa.gov/
 - Copy and paste registered key into file api.txt
 - Run this file using python
'''


now = datetime.now()



class ImageViewer:
    '''
    Simple image viewer made in pygame
    '''

    def __init__(self):

        self.root = pygame.display.set_mode((600, 450))
        pygame.display.set_caption('Space Of The Day')

        self.clock = pygame.time.Clock()
        self.running = True

        self.images = []
        self.current_image = None

        # Should the image viewer render a new frame
        self.render_new = True

        # This is probably confusing but I wanted the effect of
        # pushing left to go back in time of the images.
        self.KEY_MAP = {
            pygame.K_RIGHT: self.shift_left,
            pygame.K_LEFT: self.shift_right
        }

    def shift_left(self):
        '''Select image to the left'''

        if self.current_image is not None:
            self.current_image = max(0, self.current_image - 1)
            self.render_new = True

    def shift_right(self):
        '''Select image to the right'''

        if self.current_image is not None:
            self.current_image = min(len(self.images)-1, self.current_image + 1)
            self.render_new = True


    def scale_image(self, image):
        '''Scale image on largest axis'''

        x, y = image.get_size()
        new_x, new_y = x, y
        if x > y:
            scale = (self.root.get_size()[0] / x)
        else:
            scale = (self.root.get_size()[1] / y)
        new_x = scale * x
        new_y = scale * y

        return pygame.transform.scale(image, (int(new_x), int(new_y)))

    def add_image(self, image):
        '''Add image to buffer, select it and set it to render on next update'''

        self.images.append(image)
        self.render_new = True

        if self.current_image is None:
            self.current_image = 0
        else:
            self.current_image += 1

    def update(self):
        '''Program update, also event checking'''

        self.clock.tick(10)

        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                try:
                    self.KEY_MAP[event.key]()
                except KeyError:
                    pass

    def draw(self):
        '''If a render needs to happen re-render screen'''

        if self.render_new:
            self.root.fill((0, 0, 0))
            self.root.blit(self.images[self.current_image], (0, 0))
            self.render_new = False
            pygame.display.update()

    def run(self):
        '''Wrapping function to run image viewer'''

        while self.running:
            self.update()
            self.draw()
        pygame.quit()
        exit()

class APODViewer(ImageViewer):
    '''
    Astronomy Picture of the Day - Viewer
    Shows the picture of the day as well as allowing user
    to cycle back on previous days.

    Uses NASA's APOD API
    https://api.nasa.gov/
    '''

    APOD_url = 'https://api.nasa.gov/planetary/apod'

    def __init__(self, api_key, preload=0):

        ImageViewer.__init__(self)
        # Api Variables
        self.current_date = now.strftime('%Y-%m-%d')
        self.hd = False
        self.api_key = api_key

        # Loading text to be displayed on image loading
        self.font = pygame.font.SysFont('arial', 32)
        self.loading_label = self.font.render('Loading...', True, (255,255,255))

        self.KEY_MAP = {
            pygame.K_RIGHT: self.shift_left,
            pygame.K_LEFT: self.load_and_add
        }

        self.draw_label('Loading...')
        self.add_API_image()
        self.pre_load(preload)

    def APOD_api_req(self):
        '''
        API request function
        Returns pygame image based on current select date
        '''

        PARAMS = {'date': self.current_date,
                  'hd': str(self.hd),
                  'api_key': self.api_key}
        req = requests.get(url=APODViewer.APOD_url, params=PARAMS)
        data = req.json()

        image_res = requests.get(data['url'])
        img = Image.open(BytesIO(image_res.content))
        return pygame.image.fromstring(img.tobytes(), img.size, img.mode)

    def draw_label(self, text, pos=(0, 0)):
        '''Draw label to top left for user feedback'''

        label = self.font.render(text, True, (255,255,255))
        self.root.blit(label, pos)
        pygame.display.update()

    def pre_load(self, count):
        '''
        Hacky function to pre load images on startup so user doesn't have
        to immediately load more images.
        '''

        for i in range(count):
            self.load_and_add()
        self.current_image = 0

    def add_API_image(self):

        try:
            raw = self.APOD_api_req()
            self.add_image(self.scale_image(raw))
        except OSError:
            self.root.fill((0, 0, 0))
            self.draw_label('Error...')


    def load_and_add(self):
        '''
        Determines if it needs to load a new image from the API or can simply
        shift to an already loaded image.
        '''

        if self.current_image == len(self.images) - 1:
            self.draw_label('Loading...')
            date = datetime.strptime(self.current_date, '%Y-%m-%d')
            self.current_date = date - timedelta(days=1)
            self.current_date = self.current_date.strftime('%Y-%m-%d')
            self.add_API_image()
        else:
            self.shift_right()


if __name__ == '__main__':

    pygame.init()
    with open('api.txt', 'r') as f:
        api_key = f.read().strip('\n')
    APODViewer(api_key, preload=6).run()
