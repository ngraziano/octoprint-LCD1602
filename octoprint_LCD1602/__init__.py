# coding=utf-8

"""
  LCD1602 Plugin for Octoprint
"""

from __future__ import absolute_import
import octoprint.plugin
import octoprint.events
from RPLCD.i2c import CharLCD
import time
import datetime
import os
import sys
from fake_rpi import printf
import fake_rpi


class LCD1602Plugin(octoprint.plugin.StartupPlugin,
                    octoprint.plugin.EventHandlerPlugin,
                    octoprint.plugin.ProgressPlugin):

  def __init__(self):
    if (os.getenv('LCD1602_DOCKER')):
      print('We are running in test environnement, no i2c device attached.')
      try:
        print('Loading fake_rpi instead of smbus2')
        sys.modules['smbus2'] = fake_rpi.smbus
        self.mylcd = fake_rpi.smbus.SMBus(1)
      except:
        print('Cannot load fake_rpi !')
    else:
      self.mylcd = CharLCD(i2c_expander='PCF8574', address=0x27, cols=16, rows=2, backlight_enabled=True, charmap='A02')
      
      # create block for progress bar
      self.block = bytearray(b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF')
      self.block.append(255)
      self.mylcd.create_char(1,self.block)
    

    # create block for progress bar
    #self.mylcd.create_char(1,self.block)

  def JobIsDone(self,lcd):

    # create final anim
    self.birdy = [ '^_-' , '^_^', '-_^' , '^_^', '0_0', '-_-', '^_-', '^_^','@_@','*_*','$_$','<_<','>_>']

    for pos in range(0,13):
      lcd.cursor_pos = (1,pos)
      lcd.write_string(self.birdy[pos])
      time.sleep(0.5)
      lcd.clear()
    lcd.write_string('Job is Done    \,,/(^_^)\,,/')

      
  def on_after_startup(self):
    mylcd = self.mylcd
    self._logger.info("plugin initialized !")

  def show_temp(self,comm, parsed_temps):
    tool_temp = parsed_temps.get('T0',(None,None))[0]
    if tool_temp:
      self.mylcd.cursor_pos = (0,0)
      message = 'T:{0:3.0f}\xb0'.format(tool_temp)
      mylcd.write_string(message)
      
    return parsed_temps
  
  def on_print_progress(self,storage,path,progress):
    mylcd = self.mylcd
    
    temps = self._printer.get_current_temperatures()
    tool_temp = temps['tool0']['actual']
    
    job_data = self._printer.get_current_job()
    print_time = round(job_data["estimatedPrintTime"])

    percent = int(progress/6.25)+1
    completed = '\x01'*percent
    mylcd.clear()
    message = 'T:{0:3.0f}\xb0 P:{1:3}%'.format(tool_temp, progress)
    mylcd.write_string(message)
    mylcd.cursor_pos = (1,0)
    mylcd.write_string(completed)

    if progress<100:
      remaining=str(datetime.timedelta(seconds=print_time))
      
      mylcd.cursor_pos = (1,3)
      mylcd.write_string(remaining)

    if progress==100 :
      self.JobIsDone(mylcd)



  def on_event(self,event,payload):
    mylcd = self.mylcd
      
    if event in "Connected":
      mylcd.clear()
      mylcd.cursor_pos = (0,7)
      mylcd.write_string('Connected to:')
      mylcd.cursor_pos = (1,0)
      mylcd.write_string(payload["port"])

    if event in "Shutdown":
      mylcd.clear()
      mylcd.write_string('Bye bye ^_^')
      mylcd.backlight_enabled = False
      mylcd.close()
    
    
    if event in "PrinterStateChanged":
      
      if payload["state_string"] in "Offline":
        mylcd.clear()
        mylcd.cursor_pos = (1,0)
        mylcd.write_string('not connected')
        mylcd.backlight_enabled = False
      
      if payload["state_string"] in "Operational":
        mylcd.backlight_enabled = True
        mylcd.clear()
        mylcd.cursor_pos = (1,0)
        mylcd.write_string('Operational')
      
      if payload["state_string"] in "Cancelling":
        mylcd.clear()
        mylcd.cursor_pos = (1,0)
        mylcd.write_string('Cancelling job') 
      
      if payload["state_string"] in "PrintCancelled":
        mylcd.clear()
        mylcd.cursor_pos = (1,0)
        mylcd.write_string('Job Cancelled' ) 
      
      if payload["state_string"] in "Paused":
        mylcd.clear()
        mylcd.cursor_pos = (1,0)
        mylcd.write_string('Paused') 

      if payload["state_string"] in "Resuming":
        mylcd.clear()
        mylcd.cursor_pos = (1,0)
        mylcd.write_string('Resuming') 

  def get_update_information(self):
      return dict(
          LCD1602Plugin=dict(
              displayName="LCD1602 display",
              displayVersion=self._plugin_version,

              type="github_release",
              current=self._plugin_version,
              user="n3bojs4",
              repo="OctoPrint-Lcd1602",

              pip="https://github.com/n3bojs4/octoprint-LCD1602/archive/{target}.zip"
          )
      )

__plugin_name__ = "LCD1602 I2c display"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = LCD1602Plugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information,
    "octoprint.comm.protocol.temperatures.received": __plugin_implementation__.show_temp
	}
