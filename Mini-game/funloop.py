import pygame
import time
from pygame import gfxdraw
from collections import deque
import sys
import random
import math
import numpy as np

windowHeight = 720
windowWidth = 1080

class Asteroid:
	def __init__(self, game, x, y, dx, dy, id, image=None, radius=5):
		self.game = game
		self.x = x
		self.y = y
		self.dx = dx
		self.dy = dy
		self.radius = radius
		self.mass = math.sqrt(radius)
		self.id = id
		self.g = 100
		self.image = image

	def rect(self):
		return (self.x - self.radius, self.y - self.radius, self.radius * 2 - 2, self.radius * 2 - 2)

	def move(self):
		if self.game.first_shot:
			delta_args = self.runge_katta()
			if abs(delta_args[0]) > 0.08:
				self.x = self.x + delta_args[0]
			if abs(delta_args[1]) > 0.08:
				self.y = self.y + delta_args[1]
			self.dx = self.dx + delta_args[2]
			self.dy = self.dy + delta_args[3]

	def draw(self):
		size = self.radius * 2.0 / 1087
		asteroid = pygame.transform.rotozoom(self.image, 0, size)
		self.game.window.blit(asteroid, (self.x - self.radius, self.y - self.radius))
		# pygame.gfxdraw.aacircle(window, int(self.x), int(self.y), self.size, self.color)

	def grow(self, size, mass, x, y, dx, dy):
		if not self.radius > (size * 2):
			if (self.x - x) >= 0:
				self.x = max(self.x - size, (self.x  + x) // 2)
			else:
				self.x = min(self.x + size, (self.x  + x) // 2)

			if (self.y - y) >= 0:
				self.y = max(self.y - size, (self.y  + y) // 2)
			else:
				self.y = min(self.y + size, (self.y  + y) // 2)
		elif size >= (self.radius * 2):
			self.x = x
			self.y = y
		self.radius = max(self.radius + int(size ** 0.1), size + int(self.radius ** 0.1))
		momentum_x = dx * mass + self.dx * self.mass
		momentum_y = dy * mass + self.dy * self.mass
		self.dx = momentum_x / (mass + self.mass)
		self.dy = momentum_y / (mass + self.mass)
		self.mass += mass


	def rocket_explosion(self, size, mass, x, y, dx, dy):
		momentum_x = (dx * mass) // 2 + self.dx * self.mass
		momentum_y = (dy * mass) // 2 + self.dy * self.mass
		self.dx = momentum_x / (mass + self.mass)
		self.dy = momentum_y / (mass + self.mass)

	def runge_katta(self):
		#calculate accel at start
		k_1_accel = self.calc_accel(self.x, self.y)
		k_1_vel = (self.dx, self.dy)


		#calculate accel in the middle (k2)
		mid_coordinates = (self.x + 0.5*k_1_vel[0], self.y + 0.5*k_1_vel[1])
		k_2_accel = self.calc_accel(mid_coordinates[0], mid_coordinates[1])
		k_2_vel = (self.dx + 0.5*k_1_accel[0], self.dy + 0.5*k_1_accel[1])

		#calculate accel in the middle (k3)
		mid_coordinates_k3 = (self.x + 0.5*k_2_vel[0], self.y + 0.5*k_2_vel[1])
		k_3_accel = self.calc_accel(mid_coordinates_k3[0], mid_coordinates_k3[1])
		k_3_vel = (self.dx + 0.5*k_2_accel[0], self.dy + 0.5*k_2_accel[1])

		#calculate accel in the middle
		end_coordinates = (self.x + k_3_vel[0], self.y + k_3_vel[1])
		k_4_accel = self.calc_accel(end_coordinates[0], end_coordinates[1])
		k_4_vel = (self.dx + k_3_accel[0], self.dy + k_3_accel[1])

		delta_x = (1.0/6.0) * (k_1_vel[0] + 2.0 * (k_2_vel[0] + k_3_vel[0]) + k_4_vel[0])
		delta_y = (1.0/6.0) * (k_1_vel[1] + 2.0 * (k_2_vel[1] + k_3_vel[1]) + k_4_vel[1])
		delta_vx = (1.0/6.0) * (k_1_accel[0] + 2.0 * (k_2_accel[0] + k_3_accel[0]) + k_4_accel[0])
		delta_vy = (1.0/6.0) * (k_1_accel[1] + 2.0 * (k_2_accel[1] + k_3_accel[1]) + k_4_accel[1])

		#calculate accel 
		return (delta_x, delta_y, delta_vx, delta_vy)

	def calc_force(self, arr, x, y, sun_range=-1):
		force_magnitude_hor = 0
		force_magnitude_vert = 0
		for index in arr:
			each = arr[index]
			squared_distance = (each.x - x) ** 2 + (each.y - y) ** 2 
			if (sun_range >= 0 and math.sqrt(squared_distance) > sun_range):
				continue
			if each.id == self.id:
				continue
			distance = math.sqrt(squared_distance)
			force = (self.g * each.mass)/ (squared_distance ** 1.2)

			if abs(each.x - x) <= 0.01:
				force_y = force
				force_x = 0
			else:
				disp_y = each.y - y
				disp_x = each.x - x
				theta = math.atan(disp_y/disp_x)
				if disp_x >= 0:
					force_magnitude_hor += force*math.cos(theta)
				else:
					force_magnitude_hor -= force*math.cos(theta)

				if disp_y >= 0:
					force_magnitude_vert += force*abs(math.sin(theta))
				else:
					force_magnitude_vert -= force*abs(math.sin(theta))

		return [force_magnitude_hor, force_magnitude_vert]

	def calc_accel(self, x, y):
		sun_range = 300
		forces = self.calc_force(self.game.asteroids, x, y, 80)
		forces_rocket = self.calc_force(self.game.rockets, x, y)
		if self.id in self.game.rockets:
			sun_range = -1
		sun_arr = {0:self.game.sun}
		forces_sun = self.calc_force(sun_arr, x, y, sun_range)
		forces_black_holes = self.calc_force(self.game.black_holes, x, y, sun_range)
		forces_x = forces[0] + forces_rocket[0] + forces_sun[0] + forces_black_holes[0]
		forces_y = forces[1] + forces_rocket[1] + forces_sun[1] + forces_black_holes[1]
		accel_x = forces_x / self.mass
		accel_y = forces_y / self.mass
		return accel_x, accel_y

class Block():
	def __init__(self, game, x, y, image, id, size=40):
		self.x, self.y = x, y
		self.game = game
		self.size = size
		self.id = id
		self.color = [200, 200, 200]
		self.image = image

	def draw(self):
		block = pygame.transform.scale(self.image, (self.size, self.size))
		self.game.window.blit(block, (self.x, self.y))

	def rect(self):
		return (self.x, self.y, self.size - 5, self.size - 5)
class Rocket(Asteroid):
	def __init__(self, game, dx, dy, id, radius=3):
		self.x, self.y = 20, windowHeight // 2
		super(self.__class__, self).__init__(game, self.x, self.y, dx, dy, id, radius)
		self.game = game
		self.radius = radius
		self.dx = dx
		self.dy = dy
		self.id = id
		self.mass *= 30
		self.g *= 2
		self.color = [200, 200, 200]
		self.positions = []

	def draw(self):
		self.positions.append([self.x, self.y, 255])

		for each in self.positions:
			color = self.color + [each[2]]
			pygame.gfxdraw.aacircle(self.game.window, int(each[0]), int(each[1]), self.radius, color)
			pygame.gfxdraw.filled_circle(self.game.window, int(each[0]), int(each[1]), self.radius, color)
			each[2] -= 4
		if self.positions[0][2] <= 0:
			del self.positions[0]

	def rect(self):
		return (self.x - self.radius, self.y - self.radius, self.radius * 2 + 4, self.radius * 2 + 4)

class Sun(Asteroid):
	def __init__(self, game, id, x, y, radius=15):
		self.x, self.y = x, y
		super(self.__class__, self).__init__(game, self.x, self.y, 0, 0, id, radius)
		self.game = game
		self.radius = radius
		self.id = id
		self.mass *= 10
		self.g *= 100
		self.image = self.game.sun_image
		self.center_radius = 0

	def move(self):
		return

	def draw(self):
		self.game.window.blit(self.image, (self.x - self.radius, self.y - self.radius))
		# pygame.gfxdraw.filled_circle(self.game.window, self.x, self.y, int(self.center_radius), (255, 255, 220))


	def merge(self, asteroid):
		self.mass += asteroid.mass
		self.game.score += int(asteroid.mass * 10)
		self.center_radius = math.sqrt(max((self.mass - (7 * math.sqrt(self.radius))), 0))

	def black_merge(self, asteroid):
		self.mass += asteroid.mass
		self.game.score += int(asteroid.mass * 2)
		self.center_radius = math.sqrt(max((self.mass - (7 * math.sqrt(self.radius))), 0))



class Game:
	def __init__(self, window):
		self.window = window
		self.FPS = 200
		self.font = pygame.font.SysFont("Courier", 64, True)
		self.b_game_over = False
		self.asteroids = {}
		self.rockets = {}
		self.blocks = {}
		self.black_holes = {}
		self.bg_image = pygame.image.load("background.png").convert()
		self.asteroid_image = pygame.image.load("asteroid.png").convert_alpha()
		self.sun_image = pygame.image.load("sun2.png").convert_alpha()
		self.Earth = pygame.image.load("Earth.png").convert_alpha()
		self.black_hole_image = pygame.image.load("black_hole.png").convert_alpha()
		self.block_image = pygame.image.load("dust_cloud.png").convert_alpha()
		self.Earth = pygame.transform.rotozoom(self.Earth, 0, 0.01666666666)
		self.bg = pygame.transform.rotozoom(self.bg_image, 0, 0.5)

		self.counter = 0
		self.last_shot = 0
		self.delay = 800
		self.sun_x = 0
		self.sun_y = 0

		# self.ammo = 5
		self.asteroid_trail = []
		self.rocket_radius = 3
		self.game_over_str = "Game Over"
		self.first_shot = False
		self.success = 1
		self.score = 0
		self.shots = 0
		self.block_size = 40

	def draw_trails(self):
		trail_color = [200, 200, 200]
		for positions in self.asteroid_trail:
			for each in positions:
				color = trail_color + [each[2]]
				pygame.gfxdraw.aacircle(self.window, int(each[0]), int(each[1]), self.rocket_radius, color)
				pygame.gfxdraw.filled_circle(self.window, int(each[0]), int(each[1]), self.rocket_radius, color)
				each[2] -= 4
			if len(positions) > 0 and positions[0][2] <= 0:
				del positions[0]


	# def spawn_asteroid(self):
	# 	rand = random.randint(40, windowWidth - 40)
	# 	rand2 = random.randint(40, windowHeight - 40)
	# 	speed_x = random.randint(-1,1)
	# 	speed_y = random.randint(-1,1)
	# 	asteroid = Asteroid(self, rand, rand2, speed_x, speed_y, self.counter, self.asteroid_image, 5)
	# 	self.asteroids[self.counter] = asteroid
	# 	self.counter += 1
	# 	
	def spawn_asteroid(self, x, y, size=8):
		
		speed_x = 0
		speed_y = 0
		asteroid = Asteroid(self, x, y, speed_x, speed_y, self.counter, self.asteroid_image, size)
		self.asteroids[self.counter] = asteroid
		self.counter += 1

	def generate_asteroids(self, num):
		initial_pos = []
		for i in range(num):
			rand_x = random.randint(45, 150)
			rand_y = random.randint(30, windowHeight - 30)
			while rand_x >= windowWidth // 2 - 200 and rand_x <= windowWidth // 2 + 200 and rand_y >= windowHeight // 2 - 200 and rand_y <= windowHeight // 2 + 200:
				rand_x = random.randint(30, windowWidth - 30)
				rand_y = random.randint(30, windowHeight - 30)
			initial_pos.append([rand_x, rand_y])
		for i in range(len(initial_pos)):
			asteroid = Asteroid(self, initial_pos[i][0], initial_pos[i][1], 0, 0, self.counter, self.asteroid_image, 8)
			self.asteroids[self.counter] = asteroid
			self.counter += 1

	def generate_pattern(self):
		blocks_width = windowWidth // self.block_size
		blocks_height = windowHeight // self.block_size
		pattern_1 = np.zeros((blocks_height, blocks_width))

		#5 Wall Pattern
		for i in range(5):
			for j in range(blocks_height):
				pattern_1[j, i * 4 + 6] = 1
		for i in range(12):
			pattern_1[0, i] = 1
			pattern_1[blocks_height - 1, i] = 1
		pattern_1[blocks_height // 2, blocks_width - 4] = 2
		pattern_1[blocks_height // 4, blocks_width // 2] = 3
		pattern_1[3*blocks_height // 4, 3*blocks_width // 4] = 3

		return pattern_1
	def read_pattern(self):
		blocks_width = windowWidth // self.block_size
		blocks_height = windowHeight // self.block_size
		file = open("input.txt")
		lines = [line.rstrip("\n").split(',') for line in file.readlines()]
		pattern = np.zeros((blocks_height, blocks_width))
		for j in range(blocks_height):
			for i in range(blocks_width):
				pattern[j, i] = lines[j][i]
		return pattern

	def generate_blocks(self, pattern):
		for j in range(len(pattern)):
			for i in range(len(pattern[0])):
				if pattern[j, i] == 1:
					block = Block(self, i * self.block_size, j * self.block_size, self.block_image, self.counter, self.block_size)
					self.blocks[self.counter] = block
					self.counter += 1

				elif pattern[j, i] == 2:
					self.sun = Sun(self, self.counter, i * self.block_size, j * self.block_size)
					self.counter += 1
				elif pattern[j, i] == 3:
					black_hole = Sun(self, self.counter, i * self.block_size, j * self.block_size)
					self.counter += 1
					self.black_holes[self.counter] = black_hole
					black_hole.image = self.black_hole_image

	def check_collisions(self, rect1, rect2, already_collided = False): #rect: x, y, width, height
		if (rect1[0] >= rect2[0] and rect1[0] <= rect2[0] + rect2[2]) or (rect1[0] <= rect2[0] and rect1[0] + rect1[2] >= rect2[0]):
			if (rect1[1] >= rect2[1] and rect1[1] <= rect2[1] + rect2[3]) or (rect1[1] <= rect2[1] and rect1[1] + rect1[3] >= rect2[1]):
				if not already_collided:
					return True
		return False

	def run(self):
		clock = pygame.time.Clock()
		paused = False
		self.generate_asteroids(7)
		self.generate_blocks(self.read_pattern())
		start_time = pygame.time.get_ticks()

		while not self.b_game_over:
			asteroids_to_merge = {}
			object_removal = set()
			keys = pygame.key.get_pressed()
			mouse_press = pygame.mouse.get_pressed()[0]
			if keys[pygame.K_ESCAPE]:
				exit()
			if keys[pygame.K_q]:
				exit()
			if keys[pygame.K_u]:
				exit()
			if mouse_press and pygame.time.get_ticks() - self.last_shot >= self.delay:
				if not self.first_shot:
					self.first_shot = True
				self.last_shot = pygame.time.get_ticks()
				mouse_pos = pygame.mouse.get_pos()
				magnitude = math.sqrt(mouse_pos[0] ** 2 + ((windowHeight // 2) - mouse_pos[1]) ** 2)
				mouse_dx = mouse_pos[0] / magnitude * 3
				mouse_dy = (mouse_pos[1] - (windowHeight // 2)) / magnitude * 3
				self.rockets[self.counter] = Rocket(self, mouse_dx, mouse_dy, self.counter, self.rocket_radius)
				self.counter += 1
				self.shots += 1
				# self.ammo -= 1
			for event in pygame.event.get():
				if event.type == pygame.KEYUP:
					if event.key == pygame.K_p:
						if not paused:
							paused = True
						else:
							paused = False
					# if event.key == pygame.K_s:
					# 	self.spawn_asteroid()

				if event.type == pygame.QUIT:
					exit()
			self.window.fill((0, 0, 0, 100))

			self.window.blit(self.bg, (0,0))
			self.window.blit(self.Earth, (12, windowHeight // 2 - 10))
			self.sun.draw()

			

			for i in self.asteroids:
				each = self.asteroids[i]
				each.move()
				if each.x + each.radius <= -10 or each.x - each.radius >= windowWidth + 10:
					self.success = 0
					object_removal.add(each.id)
				elif each.y + each.radius <= -10 or each.y - each.radius >= windowHeight + 10:
					self.success = 0
					object_removal.add(each.id)

				for j in self.asteroids:
					if j == i:
						continue
					other = self.asteroids[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						if each in asteroids_to_merge:
							asteroids_to_merge[each].append(other)
						else:
							asteroids_to_merge[each] = [other]
				for j in self.blocks:
					other = self.blocks[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						each.dx *= 0.5
						each.dy *= 0.5
						object_removal.add(other.id)
			for b in self.black_holes:
				black_hole = self.black_holes[b]
				black_hole.draw()
			for b in self.blocks:
				block = self.blocks[b]
				block.draw()
			for i in self.rockets:
				each = self.rockets[i]
				each.move()
				if each.x - each.radius <= 0 or each.x + each.radius >= windowWidth or each.y - each.radius <= 0 or each.y + each.radius >= windowHeight:
					object_removal.add(each.id)
				for j in self.rockets:
					if j == i:
						continue
					other = self.rockets[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						object_removal.add(each.id)
						object_removal.add(other.id)
						self.asteroid_trail.append(each.positions)

				for j in self.asteroids:
					other = self.asteroids[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						object_removal.add(each.id)
						other.rocket_explosion(each.radius, each.mass, each.x, each.y, each.dx, each.dy)
						self.asteroid_trail.append(each.positions)

				for j in self.blocks:
					other = self.blocks[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						object_removal.add(each.id)
						object_removal.add(other.id)
						self.asteroid_trail.append(each.positions)

				for j in self.black_holes:
					other = self.black_holes[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						object_removal.add(each.id)
						self.asteroid_trail.append(each.positions)

				if self.check_collisions(each.rect(), self.sun.rect()) or self.check_collisions(self.sun.rect(), each.rect()):
					if not each.id in object_removal:
						object_removal.add(each.id)
						self.asteroid_trail.append(each.positions)
						self.score += 10*len(self.asteroids)
				each.draw()

			for each in asteroids_to_merge:
				if not each.id in object_removal:
					for other in asteroids_to_merge[each]:
						if not other.id in object_removal:
							object_removal.add(other.id)
							each.grow(other.radius, other.mass, other.x, other.y, other.dx, other.dy)

			for i in self.asteroids:
				each = self.asteroids[i]
				if self.check_collisions(each.rect(), self.sun.rect()) or self.check_collisions(self.sun.rect(), each.rect()):
					self.sun.merge(each)
					if not each.id in object_removal:
						object_removal.add(each.id)

				for j in self.black_holes:
					other = self.black_holes[j]
					if self.check_collisions(each.rect(), other.rect()) or self.check_collisions(other.rect(), each.rect()):
						other.black_merge(each)
						object_removal.add(each.id)

			for each in object_removal:
				if each in self.asteroids:
					del self.asteroids[each]
				elif each in self.rockets:
					del self.rockets[each]
				elif each in self.blocks:
					self.spawn_asteroid(self.blocks[each].x + self.blocks[each].size // 2, self.blocks[each].y + self.blocks[each].size // 2)
					del self.blocks[each]

			for each in self.asteroids:
				self.asteroids[each].draw()
			self.draw_trails()
			self.render_score()

			pygame.display.flip()
			clock.tick(self.FPS)
			curr_time = pygame.time.get_ticks()

			if len(self.asteroids) <= 0 and len(self.blocks) <= 0:
				new_time = (pygame.time.get_ticks() - start_time)//1000
				return self.game_over(), self.score, [self.shots, new_time, self.score]
	def render_score(self, color =(200,200,200)):
		score_str = "Score: " + str(self.score)
		score_font = pygame.font.SysFont("Courier", 32, True)
		score_size = self.font.size(score_str)
		render_score = score_font.render(score_str, 1, color)
		self.window.blit(render_score, (windowWidth // 2 - score_size[0] // 4, 10 + score_size[1] // 2))
	def game_over(self):
		clock = pygame.time.Clock()
		curr_time = pygame.time.get_ticks()
		while True:
			keys = pygame.key.get_pressed()
			if keys[pygame.K_ESCAPE]:
				exit()
				return False
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit()
					return False
				if event.type == pygame.KEYUP:
					if event.key == pygame.K_l:
						return True

			self.window.fill((255, 255, 255, 200))
			game_over_str_size = self.font.size(self.game_over_str)
			renderGameOver = self.font.render(self.game_over_str, 1, (0, 0, 0))
			self.window.blit(renderGameOver, (windowWidth // 2 - game_over_str_size[0] // 2, windowHeight // 2 - game_over_str_size[1] // 2))
			self.render_score((0,0,0))
			if pygame.time.get_ticks() - curr_time > 1000:
				retry_str = "Press l to see the leaderboard."
				retry_font = pygame.font.SysFont("Courier", 32, True)
				retry_size = retry_font.size(retry_str)
				render_retry = retry_font.render(retry_str, 1, (0,0,0))
				self.window.blit(render_retry, (windowWidth // 2 - retry_size[0] // 2, windowHeight // 2 + retry_size[1] // 2))

			pygame.display.flip()
			clock.tick(self.FPS)
	def tutorial(self):
		clock = pygame.time.Clock()
		curr_time = pygame.time.get_ticks()
		tutorial_str = "To step through the tutorial, press SPACE. To skip it, press S."
		tutorial_str2 = "Your Sun's energy is running out!"
		tutorial_str3 = "If you do not replenish it with asteroids, all life on Earth will perish."
		tutorial_str4 = "Clicking with your mouse will launch a comet from Earth."
		tutorial_str5 = "If you shoot the sun, you get points based on the number of asteroids on screen."
		tutorial_str6 = "Breaking a block (shoot it) will reveal an asteroid."

		instructions = [tutorial_str, tutorial_str2, tutorial_str3, tutorial_str4, tutorial_str5, tutorial_str6]
		index = 0

		while True:
			keys = pygame.key.get_pressed()
			if keys[pygame.K_ESCAPE]:
				exit()
			if keys[pygame.K_q]:
				exit()
			if keys[pygame.K_s]:
				return
			
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit()
				if event.type == pygame.KEYUP:
					if event.key == pygame.K_SPACE:
						index += 1
						if index >= len(instructions) - 1:
							return
			self.window.fill((255, 255, 255, 200))
			instruction_str = instructions[index]
			self.render_inst(instruction_str)
			# if index == 5:
			# 	self.render_inst(instructions[index + 1], 26)
			pygame.display.flip()
			clock.tick(self.FPS)
	def leaderboard(self, lines, name):
		clock = pygame.time.Clock()
		flag = False
		index = 0
		leaderboard = []
		for i in range(len(lines)):
			lines[i][1] = int(lines[i][1])
			if self.score >= lines[i][1] and not flag:
				lines[i] = [name, self.score]
				flag = True

		lines = np.array(lines)

		lines = np.sort(lines, axis=1)

		write(lines)
		while True:
			keys = pygame.key.get_pressed()
			if keys[pygame.K_ESCAPE]:
				exit()
			if keys[pygame.K_q]:
				exit()
			if keys[pygame.K_s]:
				return leaderboard
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					exit()
				if event.type == pygame.KEYUP:
					if event.key == pygame.K_SPACE:
						return leaderboard
			self.window.fill((255, 255, 255, 200))
			instruction_str = "Press SPACE to play again."
			renderFont = pygame.font.SysFont("Courier", 32, True)
			instruction_str_size = renderFont.size(instruction_str)
			renderInstruction = renderFont.render(instruction_str, 1, (0, 0, 0))
			self.window.blit(renderInstruction, (windowWidth // 2 - instruction_str_size[0] // 2, windowHeight - 48))

			leaderboard_str = "Leaderboard"
			renderFont = pygame.font.SysFont("Courier", 48, True)
			leaderboard_str_size = renderFont.size(leaderboard_str)
			renderLeaderboard = renderFont.render(leaderboard_str, 1, (0, 0, 0))
			self.window.blit(renderLeaderboard, (windowWidth // 2 - leaderboard_str_size[0] // 2, 22))
			height = 22 + leaderboard_str_size[1]

			for each in lines:
				if len(each) != 2:
					continue
				score_str = str(each[0]) + ": " + str(each[1])
				renderFont = pygame.font.SysFont("Courier", 32, True)
				score_str_size = renderFont.size(score_str)
				renderScore = renderFont.render(score_str, 1, (0, 0, 0))
				self.window.blit(renderScore, (windowWidth // 2 - score_str_size[0] // 2, height))
				height += score_str_size[1] + 4

			pygame.display.flip()
			clock.tick(self.FPS)
	def render_inst(self, instruction_str, offset=0):
		renderFont = pygame.font.SysFont("Courier", 22, True)
		instruction_str_size = renderFont.size(instruction_str)
		renderInstruction = renderFont.render(instruction_str, 1, (0, 0, 0))
		self.window.blit(renderInstruction, (windowWidth // 2 - instruction_str_size[0] // 2, windowHeight // 2 - instruction_str_size[1] // 2 + offset))

def read():
	"""Reads in the file"""
	file = open("leaderboard.txt")
	lines = [line.rstrip('\n').split(',') for line in file.readlines()]
	return lines

def write(leaderboard):
	file = open("leaderboard.txt", "w")
	file.truncate(0)
	for i in range(min(len(leaderboard), 10)):
		if len(leaderboard[i]) != 2:
			continue
		write_out = str(leaderboard[i][0]) + "," + str(leaderboard[i][1]) + "\n"
		file.write(write_out)
	file.close()

def write(shots):
	file = open("shots.txt", "a")
	for each in shots:
		file.write(str(each) + " ")
	file.write("\n")
	file.close()


def main():
	name = input("Enter your name: ")
	lines = read()
	window = pygame.display.set_mode((windowWidth, windowHeight), pygame.FULLSCREEN)
	pygame.display.set_caption("Asteroids")
	pygame.font.init()
	play = True
	while play:
		game = Game(window)
		game.tutorial()
		play, score, shots = game.run()
		write(shots)
		leaderboard = game.leaderboard(lines, name)
main()
