import pygame
import time
from pygame import gfxdraw
from collections import deque
import sys
import random
import math

windowHeight = 720
windowWidth = 1080
window = pygame.display.set_mode((windowWidth, windowHeight), pygame.FULLSCREEN)
pygame.display.set_caption("Gravity Pong")
pygame.font.init()

class Paddle:
	def __init__(self, game, direction=1): #direction 1 for left, 2 for right side
		self.game = game
		self.score = 0
		self.paddleSpeed = 10
		self.paddleWidth, self.paddleHeight = 10, 100
		self.direction = direction
		self.font = pygame.font.SysFont("Courier", 64, True)
		self.delay = 300
		self.lastShot = pygame.time.get_ticks() - 10

		if self.direction == 2:
			self.x, self.y = windowWidth - 20, windowHeight // 2 - self.paddleHeight // 2
		else:
			self.x, self.y = 20 - self.paddleWidth, windowHeight // 2 - self.paddleHeight // 2

		self.blink_colors = [(242, 228, 200), (245, 235, 215), (248, 240, 230), (252, 248, 243), (255, 255, 255)]
		self.color_index = 0

	def action(self):
		keys = pygame.key.get_pressed()
		if self.direction == 2:
			#Move right paddle Up/Down
			if keys[pygame.K_UP]: 
				self.y -= self.paddleSpeed
			elif keys[pygame.K_DOWN]:
				self.y += self.paddleSpeed

			#Fire projectile
			elif keys[pygame.K_SLASH]:
				if pygame.time.get_ticks() - self.lastShot >= self.delay:
					self.game.generate_projectile(self.x, self.y + self.paddleHeight // 2, -1)
					self.lastShot = pygame.time.get_ticks()

		else:
			#Move left paddle Up/Down
			if keys[pygame.K_w]:
				self.y -= self.paddleSpeed
			elif keys[pygame.K_s]:
				self.y += self.paddleSpeed

			#Fire projectile
			elif keys[pygame.K_f]:
				if pygame.time.get_ticks() - self.lastShot >= self.delay:
					self.game.generate_projectile(self.x, self.y + self.paddleHeight // 2, 1)
					self.lastShot = pygame.time.get_ticks()

		#Ensures paddle does not leave window
		if self.y < 4 + self.game.boundary_width:
			self.y = 4 + self.game.boundary_width
		elif self.y > windowHeight - self.paddleHeight - 4 - self.game.boundary_width:
			self.y = windowHeight - self.paddleHeight - 4 - self.game.boundary_width
	
	def draw(self):
		color = self.get_color()
		
		x, y, width, height = self.get_rekt()
		xLocationRect = x + width // 2
		xLocationEllipse = x + 10
		if self.direction == 2:
			xLocationRect = x - 2*width
			xLocationEllipse = x

		#Draw the different parts of the paddle
		pygame.gfxdraw.box(window, (x, y, width, height), color)
		pygame.gfxdraw.box(window, (xLocationRect + width // 2, y - 4 + height // 2, 15, 8), color)
		pygame.gfxdraw.aaellipse(window, xLocationEllipse, y + height // 2, 5, 8, color)
		pygame.gfxdraw.filled_ellipse(window, xLocationEllipse, y + height // 2, 5, 8, color)

	def rect(self):
		return (self.x, self.y, self.paddleWidth + 2, self.paddleHeight + 1)

	#Calculate the current color of the paddle (blinks when paddle is hit with ball)
	def get_rekt(self):
		if self.color_index % 4*(len(self.blink_colors)) != 0:
			x_change = 2*(self.color_index // 2)
			y_change = 4 * x_change
			if self.direction == 2:
				return (self.x - x_change, self.y - y_change // 2, x_change + self.paddleWidth, y_change + self.paddleHeight)
			return (self.x, self.y - y_change // 2, x_change + self.paddleWidth, y_change + self.paddleHeight)
		else:
			return self.x, self.y, self.paddleWidth, self.paddleHeight

	def get_color(self):
		if self.color_index % 4*(len(self.blink_colors)) != 0:
			return self.blink()
		else:
			self.color_index = 0
			return self.blink_colors[0]

	#Causes paddle to blink upon collision with ball
	def onCollision(self):
		if self.color_index != 0:
			self.color_index = 0
		self.blink()

	def blink(self):
		if len(self.blink_colors) < self.color_index * 2:
			color = self.blink_colors[len(self.blink_colors) - (self.color_index % len(self.blink_colors)) // 2]
		else:
			color = self.blink_colors[self.color_index // 2]
		self.color_index += 1
		return color
			

class Ball:
	def __init__(self, game, FPS, xSpeed, ySpeed, size=20, x=windowWidth//2, y=windowHeight//2):
		self.x, self.y = x, y
		self.xSpeed, self.ySpeed = xSpeed, ySpeed
		self.size = size
		self.game = game
		self.color = (20, 20, 20)
		self.max_speed = FPS
		self.projectile_speed_increase = 10
		self.ball_boundary_collision_check = [False, False, False, False, False, False]
		self.prev_position = self.x

		#Gravity modifier
		self.g = 7000

	#Handles movement to account for gravity
	def move(self):
		delta_args = self.runge_kutta()
		self.x = self.x + delta_args[0]
		self.y = self.y + delta_args[1]
		self.xSpeed = self.xSpeed + delta_args[2]
		self.ySpeed = self.ySpeed + delta_args[3]

		

		if self.x <= 0:
			self.game.increment_score(1)
		elif self.x >= windowWidth:
			self.game.increment_score(0)

	def draw(self):
		#Scales the asteroid image to size of the ball
		asteroid = pygame.transform.scale(self.game.asteroid, (self.size * 2, self.size*2))
		pygame.gfxdraw.filled_circle(window, int(self.x), int(self.y), self.size, self.color)
		window.blit(asteroid, (self.x - self.size, self.y - self.size))


	#Standard 4th order Runge-Kutta
	def runge_kutta(self):
		#calculate acceleration at start
		k_1_accel = self.calc_accel(self.x, self.y)
		k_1_vel = (self.xSpeed, self.ySpeed)


		#calculate accel in the middle (k2)
		mid_coordinates = (self.x + 0.5*k_1_vel[0], self.y + 0.5*k_1_vel[1])
		k_2_accel = self.calc_accel(mid_coordinates[0], mid_coordinates[1])
		k_2_vel = (self.xSpeed + 0.5*k_1_accel[0], self.ySpeed + 0.5*k_1_accel[1])

		#calculate accel in the middle (k3)
		mid_coordinates_k3 = (self.x + 0.5*k_2_vel[0], self.y + 0.5*k_2_vel[1])
		k_3_accel = self.calc_accel(mid_coordinates_k3[0], mid_coordinates_k3[1])
		k_3_vel = (self.xSpeed + 0.5*k_2_accel[0], self.ySpeed + 0.5*k_2_accel[1])

		#calculate accel in the middle
		end_coordinates = (self.x + k_3_vel[0], self.y + k_3_vel[1])
		k_4_accel = self.calc_accel(end_coordinates[0], end_coordinates[1])
		k_4_vel = (self.xSpeed + k_3_accel[0], self.ySpeed + k_3_accel[1])

		delta_x = (1.0/6.0) * (k_1_vel[0] + 2.0 * (k_2_vel[0] + k_3_vel[0]) + k_4_vel[0])
		delta_y = (1.0/6.0) * (k_1_vel[1] + 2.0 * (k_2_vel[1] + k_3_vel[1]) + k_4_vel[1])
		delta_vx = (1.0/6.0) * (k_1_accel[0] + 2.0 * (k_2_accel[0] + k_3_accel[0]) + k_4_accel[0])
		delta_vy = (1.0/6.0) * (k_1_accel[1] + 2.0 * (k_2_accel[1] + k_3_accel[1]) + k_4_accel[1])

		#calculate accel 
		return (delta_x, delta_y, delta_vx, delta_vy)

	#Determine acceleration based on position of the ball
	def calc_accel(self, x, y):
		distance_left = (x + 80) ** 2 + ((y - windowHeight // 2) ** 2)
		distance_right = (windowWidth - x + 80) ** 2 + (y - windowWidth // 2) ** 2
		delta_force_left = (1 / distance_left) * self.g
		delta_force_right = (1 / distance_right) * self.g
		magnitude_left = math.sqrt(distance_left)
		magnitude_right = math.sqrt(distance_right)
		straight_line_vector_left = ((- 20 - x) / magnitude_left, (windowHeight // 2 - y) / magnitude_left)
		straight_line_vector_right = ((windowWidth + 20 - x) / magnitude_right, (windowHeight // 2 - y) / magnitude_right) 
		accel_x = straight_line_vector_left[0] * delta_force_left + straight_line_vector_right[0] * delta_force_right
		accel_y = straight_line_vector_left[1] * delta_force_left + straight_line_vector_right[1] * delta_force_right
		return accel_x, accel_y

	def rect(self):
		return (self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)

	def set_direction_x(self, direction):
		self.xSpeed = abs(self.xSpeed) * direction

	#Increase speed of ball when colliding with projectiles (up to a max_speed)
	def on_projectile_collision(self, direction):
		new_speed = self.xSpeed + direction * self.projectile_speed_increase
		if not new_speed > self.max_speed:
			self.xSpeed = new_speed
		else:
			self.xSpeed = self.max_speed 

class Projectile:
	def __init__(self, game, x, y, val, direction=1):
		self.x, self.y = x, y
		self.game = game
		self.projectileWidth, self.projectileHeight = 15, 6
		self.direction = direction

		#speed of projectile in x-direction
		self.speed = 15
		self.value = val

	def move(self):
		self.x += self.speed*self.direction

		if self.x <= -40 or self.x >= windowWidth + 40:
			self.erase()

	#Removes projectile
	def erase(self):
		self.game.erase_projectile(self)

	def draw(self):
		pygame.gfxdraw.box(window, (int(self.x), int(self.y), self.projectileWidth, self.projectileHeight), (240, 126, 65))

	def rect(self):
		return (self.x, self.y, self.projectileWidth + 3, self.projectileHeight + 3)


class Game:
	def __init__(self):
		self.FPS = 100
		self.player_1_score = 0
		self.player_2_score = 0
		self.score_to_win = 5
		self.paddle1 = Paddle(self, 1)
		self.paddle2 = Paddle(self, 2)
		ball_dir = -1 + 2*random.SystemRandom().randint(0, 1)
		self.ball_size = 14
		self.asteroid = pygame.image.load("asteroid.png")
		self.balls = [Ball(self, self.FPS, ball_dir * 7, 3, self.ball_size)]
		self.projectiles = {}
		self.projectiles_to_remove = deque()
		self.font = pygame.font.SysFont("Courier", 64, True)
		self.projectile_counter = 0
		self.ball_collision_check = [False, False]
		self.boundary_width = 5
		self.b_game_over = False
		self.win_string = ''
		self.bound_color = (109, 192, 199)

		#Boolean array - stores which boundaries are currently in a 'blinking' state
		self.bound_hit = [0, 0, 0, 0, 0, 0]
		self.aBoundIndex = [0, 0, 0, 0, 0, 0]

		#Number of 'blinks' a boundary undergoes after each collision
		self.blink_iterations = 8
		self.boundaries = self.set_boundaries()


	def increment_score(self, player):
		if player == 0:
			self.player_1_score += 1	
		else:
			self.player_2_score += 1
		if self.player_1_score >= self.score_to_win or self.player_2_score >= self.score_to_win:
			win_string = "Player " + str((1- player) + 1) + " Loses!"
			self.win_string = win_string
			self.b_game_over = True
		else:
			#Reset balls upon scoring
			self.reset_balls()


	def reset_balls(self):
		if self.ball_size < 40:
			self.ball_size = int(self.ball_size * 1.1)
		ball_dir = -1 + 2*random.SystemRandom().randint(0, 1)
		self.balls = [Ball(self, self.FPS, ball_dir * 8, 3, size=self.ball_size)]

	#Display the score strings
	def render_score(self):
		scoreRender1 = self.font.render(str(self.player_1_score), 1, (255, 255, 255))
		scoreRender2 = self.font.render(str(self.player_2_score), 1, (255, 255, 255))
		window.blit(scoreRender1, (windowWidth // 4, windowHeight // 16))
		window.blit(scoreRender2, ((3*windowWidth) // 4, windowHeight // 16))

	#Collision detection - compares boundaries of two rectangles
	def check_collisions(self, rect1, rect2, already_collided = False):
		if (rect1[0] >= rect2[0] and rect1[0] <= rect2[0] + rect2[2]) or (rect1[0] <= rect2[0] and rect1[0] + rect1[2] >= rect2[0]):
			if (rect1[1] >= rect2[1] and rect1[1] <= rect2[1] + rect2[3]) or (rect1[1] <= rect2[1] and rect1[1] + rect1[3] >= rect2[1]):
				if not already_collided:
					return True
		return False


	#Create a new projectile
	def generate_projectile(self, x, y, direction):
		projectile = Projectile(self, x, y, self.projectile_counter, direction)
		self.projectiles[self.projectile_counter] = projectile
		self.projectile_counter += 1

	#Erase a projectile
	def erase_projectile(self, projectile):
		self.projectiles_to_remove.append(projectile.value)

	#Sets the top, bottom, upper left, lower left, upper right, and lower right boundaries as rectangles
	#Returns array
	def set_boundaries(self):
		top_boundary = (4,  4, windowWidth - 8, self.boundary_width)
		bot_boundary = (4,  windowHeight - self.boundary_width - 4, windowWidth - 8, self.boundary_width)
		boundary_range = int(1.1*(windowHeight // 4) - 4)
		left_boundary_top = (3, 4, self.boundary_width, boundary_range)
		left_boundary_bot = (3, windowHeight - boundary_range - 4, self.boundary_width, boundary_range)
		right_boundary_top = (windowWidth - self.boundary_width - 3, 4, self.boundary_width, boundary_range)
		right_boundary_bot = (windowWidth - self.boundary_width - 3, windowHeight - boundary_range - 4, self.boundary_width, boundary_range)

		return [top_boundary, bot_boundary, left_boundary_top, left_boundary_bot, right_boundary_top, right_boundary_bot]

	#Remove a ball from the screen
	def remove_ball(self, ball):
		self.balls.remove(ball)

	#Split a ball into two separate balls (occurs upon collision with projectile)
	def ball_split(self, ball):
		if ball.size >= 10:
			new_ball = Ball(self, self.FPS, ball.xSpeed, ball.ySpeed, math.floor(ball.size / 1.25) , ball.x, ball.y)
			ball.size = math.floor(ball.size / 1.25)
			return new_ball
		else:
			self.remove_ball(ball)
			if len(self.balls) <= 0:
				self.font = pygame.font.SysFont("Courier", 48, True)

				win_string = "Congratulations! Both players win!"
				self.win_string = win_string
				self.b_game_over = True


	#Checks for collision with boundaries
	def boundary_collision_check(self, ball):
		for each in range(len(self.boundaries)):
			collision = self.check_collisions(ball.rect(), self.boundaries[each])
			if collision and not ball.ball_boundary_collision_check[each]:
				ball.ball_boundary_collision_check[each] = True
				self.boundary_hit(each)

				#Reflects ball upon hitting a boundary
				if each == 0 or each == 1:
					ball.ySpeed *= -1

				else:
					ball.xSpeed *= -1
			else:
				ball.ball_boundary_collision_check[each] = False


	#Draws all the boundaries
	def draw_boundaries(self, boundaries):
		for i in range(len(boundaries)):
			if self.bound_hit[i] == 1:
				color = self.boundary_blink(self.aBoundIndex[i])
				self.aBoundIndex[i] += 1
			else:
				color = self.bound_color
			if self.aBoundIndex[i] >= self.blink_iterations * 2:
				self.bound_hit[i] = 0
				self.aBoundIndex[i] = 0

			pygame.gfxdraw.box(window, boundaries[i], color)

	#Determines color of blink animation
	def boundary_blink(self, index):
		index = index % self.blink_iterations
		dr = (255 - self.bound_color[0]) // (self.blink_iterations // 2)
		dg = (255 - self.bound_color[1]) // (self.blink_iterations // 2)
		db = (255 - self.bound_color[2]) // (self.blink_iterations // 2)
		if index >= self.blink_iterations // 2:
			color = (255 - ((index % (self.blink_iterations // 2)) * dr), 255 - ((index % (self.blink_iterations // 2)) * dg), 255 - ((index % (self.blink_iterations // 2)) * db))
		else:
			color = (self.bound_color[0] + index * dr, self.bound_color[1] + index * dg, self.bound_color[2] + index * db)
		return color

	#Handles boundary collision
	def boundary_hit(self, i_boundary):
		self.bound_hit[i_boundary] = 1
		self.aBoundIndex[i_boundary] = 0
		
	#Game loop
	def run(self):
		clock = pygame.time.Clock()
		paused = False
		while not self.b_game_over:
			keys = pygame.key.get_pressed()
			#Exit game with ESC or U
			if keys[pygame.K_ESCAPE]:
				exit()
			if keys[pygame.K_u]:
				exit()
			for event in pygame.event.get():
				if event.type == pygame.KEYUP:
					#Pause game
					if event.key == pygame.K_p:
						if not paused:
							paused = True
						else:
							paused = False
				if event.type == pygame.QUIT:
					exit()
			#Set bg color
			window.fill((20, 20, 20))
			boundaries = self.set_boundaries()
			self.draw_boundaries(boundaries)
			if not paused:
				self.paddle1.action()
				self.paddle2.action()
				for ball in self.balls:
					ball.move()
					self.boundary_collision_check(ball)
					
					#Check collisions of balls with the paddles
					if self.check_collisions(ball.rect(), self.paddle1.rect(), self.ball_collision_check[0]) or self.check_collisions(self.paddle1.rect(), ball.rect(), self.ball_collision_check[0]):
						self.ball_collision_check[0] = True
						ball.set_direction_x(1)
						self.paddle1.onCollision()
					else:
						self.ball_collision_check[0] = False

					if self.check_collisions(ball.rect(), self.paddle2.rect(), self.ball_collision_check[1]) or self.check_collisions(self.paddle2.rect(), ball.rect(), self.ball_collision_check[1]):
						self.ball_collision_check[1] = True
						ball.set_direction_x(-1)
						self.paddle2.onCollision()
					else:
						self.ball_collision_check[1] = False
			
			self.render_score()
			
			new_balls = []
			for each in self.projectiles:
				projectile = self.projectiles[each]
				projectile.move()
				if not paused:
					projectile.draw()
					#Check collision of projectile with the balls
					for ball in self.balls:
						if (self.check_collisions(ball.rect(), projectile.rect()) or self.check_collisions(projectile.rect(), ball.rect())) and each not in self.projectiles_to_remove:
							projectile.erase()
							new_ball = self.ball_split(ball)
							if new_ball:
								new_balls.append(new_ball)
							ball.on_projectile_collision(projectile.direction)
			for each in new_balls:
				self.balls.append(each)

			#Remove projectiles that have collided with a ball
			for each in self.projectiles_to_remove:
				del self.projectiles[each]

			self.projectiles_to_remove.clear()
			for each in self.balls:
				each.draw()
			self.paddle1.draw()
			self.paddle2.draw()
			pygame.display.flip()
			clock.tick(self.FPS)
		curr_time = pygame.time.get_ticks()

		while self.b_game_over:

			keys = pygame.key.get_pressed()
			if keys[pygame.K_ESCAPE]:
				self.b_game_over = False
				exit()
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					self.b_game_over = False
					exit()

			#Game over screen
			window.fill((255, 255, 255))
			win_str_size = self.font.size(self.win_string)
			renderWin = self.font.render(self.win_string, 1, (0, 0, 0))
			window.blit(renderWin, (windowWidth // 2 - win_str_size[0] // 2, windowHeight // 2 - win_str_size[1] // 2))

			#Reset game
			if pygame.time.get_ticks() - curr_time > 1000:
				retry_str = "Press SPACE to play again."
				retry_font = pygame.font.SysFont("Courier", 32, True)
				retry_size = retry_font.size(retry_str)
				render_retry = retry_font.render(retry_str, 1, (0,0,0))
				window.blit(render_retry, (windowWidth // 2 - retry_size[0] // 2, windowHeight // 2 + retry_size[1] // 2))

				if keys[pygame.K_SPACE]:
					self.b_game_over = False
			pygame.display.flip()
			clock.tick(self.FPS)
		main()

def main():
	game = Game()
	game.run()
main()

