#!/usr/bin/env python

from __future__ import division
from random import randrange, choice, sample
import socket
import argparse
import pygame
import math
import gc
import sys
import time
import os

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from pycogworks.fixation import FixationProcessor
sys.path.append( "PyViewX" )
from pyviewx import iViewXClient, Dispatcher

class World( object ):
	"""Task Environment"""

	d = Dispatcher()

	def __init__( self, args, subjectInfo ):
		super( World, self ).__init__()

		self.args = args

		self.lc = None
		self.fix_data = None
		self.eye_position = None

		self.colors = [( 204, 255, 102 ), ( 255, 153, 255 )]
		if args.color:
			self.colors = self.colors[::-1]
		self.bgcolor = ( 0, 0, 0 )
		self.fix_shape = u'\u25CB'

		self.replicates = 10
		self.trialPool = self.generateTrialPool( self.replicates )
		self.blockLength = len( self.trialPool )
		self.lastTrial = self.blockLength * int( self.args.blocks )
		self.colorSetup = 1
		if self.args.color:
			self.colorSetup = 2

		self.subjectInfo = subjectInfo

		self.screenshot = 1

		self.logdir = args.logdir
		if not os.path.exists( self.logdir ):
			os.makedirs( self.logdir )

		if self.subjectInfo:
			eid = rin2id( subjectInfo['rin'] )
			subjectInfo['encrypted_rin'] = eid
			subjectInfo['cipher'] = 'AES/CBC (RIJNDAEL) - 16Byte Key'
			self.log_basename = cwsubject.makeLogFileBase( 'SaccadeTask_' + eid[:8] )
			cwsubject.writeHistoryFile( os.path.join( self.logdir, self.log_basename ), self.subjectInfo )
			self.output = open( os.path.join( self.logdir, self.log_basename ) + '.log', 'w' )
		else:
			if self.args.logfile:
				self.output = open( args.logfile, 'w' )
			else:
				self.output = sys.stdout

		if self.args.eyetracker:
			self.client = iViewXClient( self.d, self.args.eyetracker, 4444 )
			self.fp = FixationProcessor( 3.55, sample_rate = 500 )
			self.calibrationPoints = []
			self.currentPoint = -1
			self.calibrationResults = []

		pygame.mouse.set_visible( False )
		if self.args.fullscreen:
			self.screen = pygame.display.set_mode( ( 0, 0 ), pygame.FULLSCREEN )
		else:
			self.screen = pygame.display.set_mode( ( 1024, 768 ), 0 )
		self.width, self.height = self.screen.get_size()
		self.center_x = int( self.width / 2 )
		self.center_y = int( self.height / 2 )
		self.offset = int( self.width / 3 )
		self.offsets = [int( self.center_x - self.offset ), int( self.center_x + self.offset )]
		self.worldsurf = self.screen.copy()
		self.worldsurf_rect = self.worldsurf.get_rect()
		obj_width = int( self.center_y * self.args.arrowsize )
		self.fontname = 'DejaVuSansMono.ttf'
		self.obj_widths = [obj_width, int( math.ceil( obj_width * 1.5 ) ), int( math.ceil( obj_width * 2 ) )]
		self.arrow_font = pygame.font.Font( self.fontname, self.obj_widths[0] )
		self.mask_font = pygame.font.Font( self.fontname, int( self.obj_widths[2] * 1.5 ) )
		self.demo_font = pygame.font.Font( self.fontname, int( self.obj_widths[2] * 4 ) )
		self.cue_fonts = [pygame.font.Font( self.fontname, self.obj_widths[0] ),
						  pygame.font.Font( self.fontname, self.obj_widths[1] ),
						  pygame.font.Font( self.fontname, self.obj_widths[2] )]
		self.arrows = ['', u'\u25B6', u'\u25B2', u'\u25C0']
		self.arrow_text = ['', '>', '^', '<']
		self.clock = pygame.time.Clock()
		self.accuracy = []

		self.EVENT_SHOW_CUE = pygame.USEREVENT + 1
		self.EVENT_SHOW_ARROW = pygame.USEREVENT + 2
		self.EVENT_SHOW_MASK = pygame.USEREVENT + 3
		self.EVENT_HIDE_FIX = pygame.USEREVENT + 4

		self.mode_text = ''

		self.trial = 0
		self.size = self.cue_side = self.fix_delay = -1
		self.answer = self.mask_time = self.cue_time = self.trial_stop = self.trial_start = 0

	def generateTrialPool( self, n ):
		return sample( [1, 2, 3, 4] * n, 4 * n )

	def getNextPoolTrial( self ):
		if len( self.trialPool ) < 1:
			self.trialPool = self.generateTrialPool( self.replicates )
		return self.trialPool.pop()

	def get_fixation_interval( self ):
		return randrange( 1500, 3500, 1 )

	def draw_arrow( self, type, size, x ):
		self.draw_text( self.arrows[type], self.arrow_font, ( 0, 0, 0 ), ( x, self.center_y ) )

	def draw_mask( self, x ):
		self.draw_text( u'\u25A9', self.mask_font, ( 128, 128, 128 ), ( x, self.center_y ) )

	def draw_cue( self, x, size ):
		self.draw_text( u'\u25CF', self.cue_fonts[size], ( 0, 0, 0 ), ( x, self.center_y ) )

	def draw_fixation_circle( self ):
		if self.show_fix:
			self.draw_text( self.fix_shape, self.cue_fonts[0], ( 0, 0, 0 ), ( self.center_x, self.center_y ) )

	def draw_text( self, text, font, color, loc ):
		t = font.render( text, True, color )
		tr = t.get_rect()
		tr.center = loc
		self.worldsurf.blit( t, tr )

	def clear( self ):
		self.worldsurf.fill( self.bgcolor )

	def update_world( self ):
		self.screen.blit( self.worldsurf, self.worldsurf_rect )
		pygame.display.flip()

	@d.listen( 'ET_CAL' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		self.calibrationPoints = [None] * int( inResponse[0] )

	@d.listen( 'ET_CSZ' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		pass#mode = -2

	@d.listen( 'ET_PNT' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		self.calibrationPoints[int( inResponse[0] ) - 1] = ( int( inResponse[1] ), int( inResponse[2] ) )

	@d.listen( 'ET_CHG' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		self.currentPoint = int( inResponse[0] ) - 1

	@d.listen( 'ET_VLS' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		self.calibrationResults.append( inResponse )

	@d.listen( 'ET_CSP' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		pass

	@d.listen( 'ET_FIN' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		self.state = -2
		self.client.requestCalibrationResults()
		self.client.validateCalibrationAccuracy()

	@d.listen( 'ET_SPL' )
	def iViewXEvent( self, inSender, inEvent, inResponse ):
		self.eye_position = map( float, inResponse[10:] )
		if self.state < 0:
			return
		self.fix_data = self.fp.detect_fixation( int( float( inResponse[4] ) ) > 0, float( inResponse[2] ), float( inResponse[4] ) )
		if self.trial_start != 0 and self.trial_stop == 0:
			if self.trial_start == -1:
				self.trial_start = int( inResponse[0] )
			result = [time.time(), self.trial, self.mode_text, self.center_x, self.center_y,
					  self.offset, self.fix_delay, self.obj_widths[self.size],
					  self.cue_side, self.arrow_text[self.answer], self.fix_data.gaze_found, int( inResponse[0] ),
					  int( inResponse[0] ) - self.trial_start, int( self.fix_data.gaze_x ), int( self.fix_data.gaze_y )]
			self.output.write( "%f\tEVENT_SMI\tSAMPLE_IN\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t\t\t\t\t\t%d\t%d\t%d\t%d\t%d\n" % tuple( result ) )
		else:
			result = [time.time(), self.trial, self.mode_text, self.center_x, self.center_y,
					  self.offset, self.fix_delay, self.obj_widths[self.size],
					  self.cue_side, self.arrow_text[self.answer], self.fix_data.gaze_found, int( inResponse[0] ),
					  int( inResponse[0] ) - self.trial_start, int( self.fix_data.gaze_x ), int( self.fix_data.gaze_y )]
			self.output.write( "%f\tEVENT_SMI\tSAMPLE_OUT\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t\t\t\t\t\t%d\t%d\t%d\t%d\t%d\n" % tuple( result ) )
		if self.cue_time > 0:
			if self.fix_data.eye_motion_state == 2 and self.saccade_latency == 0:
				self.saccade_latency = time.time() - self.cue_time
			elif self.saccade_latency > 0 and self.saccade_direction == 'none':
				if self.fix_data.gaze_x < self.center_x:
					self.saccade_direction = 'left'
				else:
					self.saccade_direction = 'right'

	def process_events( self ):
		ret = False
		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				ret = True
				if event.key == pygame.K_ESCAPE:
					if len( self.accuracy ) > 0:
						self.do_stats()
					self.lc.stop()
					return
				if self.state == -3 and event.key == pygame.K_SPACE:
					self.client.acceptCalibrationPoint()
				elif self.state == -2:
					if event.key == pygame.K_r:
						self.calibrationResults = []
						self.state = -3
						self.client.startCalibration( 9 )
					elif event.key == pygame.K_SPACE:
						self.state = -1
				elif self.state == -1:
					self.state = 0
				elif self.state == 5:
					if event.key == pygame.K_LEFT or event.key == pygame.K_UP or event.key == pygame.K_RIGHT:
						self.trial_stop = -1
						rt = time.time() - self.target_time
						result = [time.time(), self.trial, self.mode_text, self.colorSetup, self.center_x, self.center_y, self.offset, self.fix_delay, self.obj_widths[self.size], self.cue_side, self.arrow_text[self.answer]]
						if event.key == pygame.K_LEFT:
							result.append( '<' )
							if self.answer == 3:
								result.append( 1 )
							else:
								result.append( 0 )
						elif event.key == pygame.K_UP:
							result.append( '^' )
							if self.answer == 2:
								result.append( 1 )
							else:
								result.append( 0 )
						elif event.key == pygame.K_RIGHT:
							result.append( '>' )
							if self.answer == 1:
								result.append( 1 )
							else:
								result.append( 0 )
						result.append( rt )
						self.trial_stop = time.time()
						self.state = 0
						if self.args.eyetracker:
							result.append( self.saccade_direction )
							result.append( self.saccade_latency )
							self.output.write( "%f\tEVENT_SYSTEM\tRESULT\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%d\t%f\t%s\t%d\n" % tuple( result ) )
						else:
							self.output.write( "%f\tEVENT_SYSTEM\tRESULT\t%d\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%d\t%f\n" % tuple( result ) )
						self.output.write( "%f\tEVENT_SYSTEM\tTRIAL_END\n" % ( time.time() ) )
						self.accuracy.append( result )
			elif event.type == self.EVENT_HIDE_FIX:
				self.output.write( "%f\tEVENT_SYSTEM\tHIDE_FIX\n" % ( time.time() ) )
				pygame.time.set_timer( self.EVENT_HIDE_FIX, 0 )
				self.show_fix = False
			elif event.type == self.EVENT_SHOW_CUE:
				self.output.write( "%f\tEVENT_SYSTEM\tSHOW_CUE\n" % ( time.time() ) )
				pygame.time.set_timer( self.EVENT_SHOW_CUE, 0 )
				self.state = 3
				pygame.time.set_timer( self.EVENT_SHOW_ARROW, 400 )
				self.cue_time = time.time()
				self.trial_start = -1
			elif event.type == self.EVENT_SHOW_ARROW:
				self.output.write( "%f\tEVENT_SYSTEM\tSHOW_ARROW\n" % ( time.time() ) )
				pygame.time.set_timer( self.EVENT_SHOW_ARROW, 0 )
				self.state = 4
				pygame.time.set_timer( self.EVENT_SHOW_MASK, 150 )
				self.target_time = time.time()
			elif event.type == self.EVENT_SHOW_MASK:
				self.output.write( "%f\tEVENT_SYSTEM\tSHOW_MASK\n" % ( time.time() ) )
				pygame.time.set_timer( self.EVENT_SHOW_MASK, 0 )
				self.state = 5
		self.mask_time = time.time()
		return ret

	def draw_calibration( self ):
		self.worldsurf.fill( ( 51, 51, 153 ) )
		if self.state == -3:
			if self.eye_position and self.eye_position[4] > 600 and self.eye_position[5] > 600 and self.eye_position[4] < 800 and self.eye_position[5] < 800:
				left = ( self.eye_position[0] / 99.999 * self.center_x + self.center_x, self.eye_position[2] / -99.999 * self.center_y + self.center_y )
				right = ( self.eye_position[1] / 99.999 * self.center_x + self.center_x, self.eye_position[3] / -99.999 * self.center_y + self.center_y )
				l = int( ( 700 - self.eye_position[4] ) / 5 + 20 )
				r = int( ( 700 - self.eye_position[5] ) / 5 + 20 )
				pygame.draw.circle( self.worldsurf, ( 255, 255, 255 ), map( int, left ), l )
				pygame.draw.circle( self.worldsurf, ( 255, 255, 255 ), map( int, right ), r )
			if not self.currentPoint < 0:
				pygame.draw.circle( self.worldsurf, ( 255, 255, 0 ), self.calibrationPoints[self.currentPoint], 8 )
				pygame.draw.circle( self.worldsurf, ( 0, 0, 0 ), self.calibrationPoints[self.currentPoint], 2 )
		if self.state == -2:
			f = pygame.font.Font( None, 28 )
			if not self.calibrationResults:
				t = f.render( 'Calculating calibration accuracy...', True, ( 255, 255, 255 ) )
				t_rect = t.get_rect()
				t_rect.centerx = self.center_x
				t_rect.centery = self.center_y
				self.worldsurf.blit( t, t_rect )
			else:
				t = f.render( ' '.join( self.calibrationResults[0] ), True, ( 255, 255, 255 ) )
				t_rect = t.get_rect()
				t_rect.centerx = self.center_x
				t_rect.centery = self.center_y
				self.worldsurf.blit( t, t_rect )
				if len( self.calibrationResults ) > 1:
					t = f.render( ' '.join( self.calibrationResults[1] ), True, ( 255, 255, 255 ) )
					t_rect = t.get_rect()
					t_rect.centerx = self.center_x
					t_rect.centery = self.center_y + 30
					self.worldsurf.blit( t, t_rect )
				t = f.render( "Press 'R' to recalibrate, press 'Space Bar' to continue..." , True, ( 255, 255, 255 ) )
				t_rect = t.get_rect()
				t_rect.centerx = self.center_x
				t_rect.centery = self.height - 60
				self.worldsurf.blit( t, t_rect )

	def draw_fix( self ):
		if self.fix_data:
			pygame.draw.circle( self.worldsurf, ( 0, 228, 0 ), ( int( self.fix_data.fix_x ), int( self.fix_data.fix_y ) ), 5, 0 )

	def draw_world( self ):
		self.clear()
		if self.state == -3 or self.state == -2:
			self.draw_calibration()
		elif self.state == -1:
			self.show_intro()
		elif self.state == 1 or self.state == 2:
			self.draw_fixation_circle()
		elif self.state == 3:
			self.draw_cue( self.loc1, self.size )
		elif self.state == 4:
			self.draw_arrow( self.answer, self.obj_widths[0], self.loc2 )
		elif self.state == 5:
			self.draw_mask( self.loc2 )
		if self.args.eyetracker and self.args.showfixation:
			self.draw_fix()
		self.update_world()

	def generate_trial( self ):
		self.size = self.cue_side = self.fix_delay = -1
		self.answer = self.target_time = self.mask_time = self.cue_time = self.trial_stop = self.trial_start = 0
		self.show_fix = True
		self.fix_shape = u'\u25CB'
		self.saccade_latency = 0
		self.saccade_direction = 'none'
		self.answer = choice( [3, 2, 1] )
		self.size = 0#choice([2,1,0])
		self.fix_color = ( 255, 255, 0 )
		if self.args.balanced:
			trial = self.getNextPoolTrial()
			if trial < 3:
				self.loc1 = self.offsets[0]
				self.loc2 = self.offsets[1]
			else:
				self.loc1 = self.offsets[1]
				self.loc2 = self.offsets[0]
			if trial % 2 == 0:
				self.mode_text = 'anti'
				self.bgcolor = self.colors[0]
			else:
				self.mode_text = 'pro'
				self.bgcolor = self.colors[1]
				self.loc2 = self.loc1
		else:
			self.loc1, self.loc2 = sample( self.offsets, 2 )
			self.mode_text = 'anti'
			self.bgcolor = self.colors[0]
			if self.args.mode == 'pro':
				self.bgcolor = self.colors[1]
				self.loc2 = self.loc1
				self.mode_text = 'anti'
			elif self.args.mode == 'random':
				self.loc2 = sample( self.offsets, 1 )[0]
				if self.loc1 == self.loc2:
					self.mode_text = 'pro'
					self.bgcolor = self.colors[1]
				else:
					self.mode_text = 'anti'
					self.bgcolor = self.colors[0]
		self.cue_side = 'left'
		if self.loc1 > self.center_x:
			self.cue_side = 'right'
		self.trial += 1

	def showPauseScreen( self ):
		ifont1 = pygame.font.Font( None, 34 )
		self.bgcolor = ( 0, 0, 0 )
		self.clear()
		self.draw_text( 'Take a moment to relax your eyes!', ifont1, ( 255, 255, 255 ), ( self.center_x, self.center_y - 40 ) )
		self.draw_text( 'Press any key to continue when ready...', ifont1, ( 255, 255, 255 ), ( self.center_x, self.center_y ) )
		self.update_world()
		while ( True ):
			for event in pygame.event.get():
				if event.type == pygame.KEYDOWN:
					return

	def show_intro( self ):
		ifont1 = pygame.font.Font( None, 34 )
		ifont2 = pygame.font.Font( None, 24 )
		self.draw_text( u'\u25A0', self.demo_font, self.colors[0], ( self.center_x / 2, self.center_y / 8 * 4 ) )
		self.draw_text( 'Look away from cue!', ifont1, ( 255, 255, 255 ), ( self.center_x / 2, self.center_y / 8 * 6.5 ) )
		self.draw_text( u'\u25A0', self.demo_font, self.colors[1], ( self.center_x + self.center_x / 2, self.center_y / 8 * 4 ) )
		self.draw_text( 'Look towards cue!', ifont1, ( 255, 255, 255 ), ( self.center_x + self.center_x / 2, self.center_y / 8 * 6.5 ) )
		intro = ifont2.render( "Press Any Key To Begin", True, ( 255, 255, 255 ) )
		intro_rect = intro.get_rect()
		intro_rect.centerx = self.center_x
		intro_rect.centery = int( self.center_y / 2 * 3 )
		self.worldsurf.blit( intro, intro_rect )

	def do_stats( self ):
		pass

	def refresh( self ):
		if self.state == 0:
			if self.trial == self.lastTrial:
				if len( self.accuracy ) > 0:
					self.do_stats()
				self.cleanup()
			elif self.trial > 0 and self.trial % self.blockLength == 0:
				self.showPauseScreen()
			self.generate_trial()
			self.output.write( "%f\tEVENT_SYSTEM\tTRIAL_START\n" % ( time.time() ) )
			if self.args.eyetracker:
				self.state = 1
			else:
				self.state = 2
				self.fix_delay = self.get_fixation_interval()
				pygame.time.set_timer( self.EVENT_SHOW_CUE, self.fix_delay )
				if not self.args.nogap:
					pygame.time.set_timer( self.EVENT_HIDE_FIX, self.fix_delay - 233 )
		elif self.state == 1:
			if self.fix_data:
				xdiff = abs( self.fix_data.fix_x - self.center_x )
				ydiff = abs( self.fix_data.fix_y - self.center_y )
				if xdiff <= 100 and ydiff <= 100:
					self.fix_color = ( 0, 255, 0 )
					self.fix_shape = u'\u25C9'
					if self.fix_data.fix_duration > 0: # Means at least 100ms
						self.state = 2
						self.fix_delay = self.get_fixation_interval()
						pygame.time.set_timer( self.EVENT_SHOW_CUE, self.fix_delay )
						if not self.args.nogap:
							pygame.time.set_timer( self.EVENT_HIDE_FIX, self.fix_delay - 233 )
			else:
				self.fix_color = ( 255, 255, 0 )
				self.fix_shape = u'\u25CB'
		elif self.state == 2 and self.args.eyetracker:
			if self.fix_data:
				xdiff = abs( self.fix_data.fix_x - self.center_x )
				ydiff = abs( self.fix_data.fix_y - self.center_y )
				if xdiff > 100 or ydiff > 100:
					self.output.write( "%f\tEVENT_SYSTEM\tTRIAL_RESET\n" % ( time.time() ) )
					#sys.stderr.write('False start, resetting trial.\n')
					pygame.time.set_timer( self.EVENT_SHOW_CUE, 0 )
					pygame.time.set_timer( self.EVENT_HIDE_FIX, 0 )
					self.state = 1
					self.fix_color = ( 255, 0, 0 )
					self.fix_shape = u'\u25CB'
					self.show_fix = True
			elif not self.fix_data.gaze_found:
				self.output.write( "%f\tEVENT_SYSTEM\tTRIAL_RESET\n" % ( time.time() ) )
				#sys.stderr.write('Lost gaze, resetting trial.\n')
				pygame.time.set_timer( self.EVENT_SHOW_CUE, 0 )
				pygame.time.set_timer( self.EVENT_HIDE_FIX, 0 )
				self.state = 1
				self.fix_color = ( 255, 0, 0 )
				self.fix_shape = u'\u25CB'
				self.show_fix = True
		self.draw_world()
		self.process_events()

	def run( self ):
		self.state = -1
		if self.args.eyetracker:
			self.state = -3
			self.output.write( 'clock\tevent_type\tevent_details\ttrial\tmode\tsetup\tcenter_x\tcenter_y\toffset\tfix_delay\tcue_size\tcue_side\ttarget\tresponse\tcorrect\trt\t1st_saccade_direction\t1st_saccade_latency\tgaze_found\ttimestamp\ttrial_time\tgaze_x\tgaze_y\n' )
			reactor.listenUDP( 5555, self.client )
			reactor.callLater( 0, self.client.stopEyeVideoStreaming )
			reactor.callLater( 0, self.client.setDataFormat, '%TS %ET %SX %SY %DX %DY %EX %EY %EZ' )
			reactor.callLater( 0, self.client.startDataStreaming )
			reactor.callLater( 0, self.client.setSizeCalibrationArea, self.width, self.height )
			reactor.callLater( 0, self.client.setCalibrationParam, 1, 1 )
			reactor.callLater( 0, self.client.setCalibrationParam, 2, 0 )
			reactor.callLater( 0, self.client.setCalibrationParam, 3, 1 )
			reactor.callLater( 0, self.client.setCalibrationCheckLevel, 3 )
			reactor.callLater( 0, self.client.startCalibration, 9 )
		else:
			self.output.write( 'clock\tevent_type\tevent_details\ttrial\tmode\tsetup\tcenter_x\tcenter_y\toffset\tfix_delay\tcue_size\tcue_side\ttarget\tresponse\tcorrect\trt\n' )
		self.lc = LoopingCall( self.refresh )
		d = self.lc.start( 1.0 / 30 )
		d.addCallbacks( self.cleanup )
		reactor.run()

	def cleanup( self, *args, **kwargs ):
		if self.args.logfile:
			self.output.close()
		reactor.stop()

if __name__ == '__main__':

	parser = argparse.ArgumentParser( formatter_class = argparse.ArgumentDefaultsHelpFormatter )
	parser.add_argument( '-F', '--fullscreen', action = "store_true", dest = "fullscreen", help = 'Run in fullscreen mode.' )
	parser.add_argument( '-L', '--log', action = "store", dest = "logfile", help = 'Pipe results to file instead of stdout.' )
	parser.add_argument( '-a', '--arrowsize', action = "store", dest = "arrowsize", default = 0.07, help = 'Arrow size in terms of fraction of screen height.' )
	parser.add_argument( '-m', '--mode', action = "store", dest = "mode", default = 'random', help = 'Run in pro-saccade mode instead of anti-saccade mode.' )
	parser.add_argument( '-b', '--balanced', action = "store_true", dest = "balanced", help = 'Counter-balance trials.' )
	parser.add_argument( '-B', '--blocks', action = "store", dest = "blocks", default = 12, help = 'Number of blocks to run in balanced mode.' )
	parser.add_argument( '-D', '--logdir', action = "store", dest = "logdir", default = 'data', help = 'Log dir' )
	parser.add_argument( '-n', '--nogap', action = "store_true", dest = "nogap", help = "Don't do gap trials" )
	parser.add_argument( '-c', '--color', action = "store_true", dest = "color", help = 'Set to switch anti/pro bg colors.' )

	try:
		from pycogworks.eyegaze import *
		parser.add_argument( '-e', '--eyetracker', action = "store", dest = "eyetracker", help = 'Use eyetracker.' )
		parser.add_argument( '-f', '--fixation', action = "store_true", dest = "showfixation", help = 'Overlay fixation.' )
	except ImportError:
		pass

	subjectInfo = False
	try:
		import pycogworks.cwsubject as cwsubject
		from pycogworks.util import rin2id
		parser.add_argument( '-S', '--subject', action = "store_true", dest = "subject", help = 'Get CogWorks subject info.' )
		subjectInfo = True
	except ImportError:
		pass

	args = parser.parse_args()

	if args.eyetracker:
		try:
			socket.inet_aton( args.eyetracker )
		except socket.error:
			print 'Error: Invalid IP address.'
			sys.exit()
	elif args.showfixation:
		print 'Error: Must enable eyetracker for fixation overlay'
		sys.exit()

	if args.mode == 'anti' or args.mode == 'pro' or args.mode == 'random':
		pass
	else:
		print "Error: Valid modes are: 'anti', 'pro' or 'random'"
		sys.exit()

	if subjectInfo and args.subject:
		subjectInfo = cwsubject.getSubjectInfo( minimal = True )
		if not subjectInfo:
			sys.exit()
	else:
		subjectInfo = False

	gc.disable()
	pygame.display.init()
	pygame.font.init()

	w = World( args, subjectInfo )
	w.run()
