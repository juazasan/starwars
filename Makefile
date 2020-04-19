prepare:
	sudo apt install v4l2loopback-dkms -y
	sudo modprobe -r v4l2loopback
	sudo modprobe v4l2loopback devices=1 video_nr=20 card_label="v4l2loopback" exclusive_caps=1
	sudo groupadd $USER video
	docker network create --drive bridge fakecam
build-bodypix:
	docker build -t bodypix ./bodypix
build-bodypixgpu:
	docker build -t bodypixgpu ./bodypixgpu
build-fakecam:
	docker build -t fakecam ./fakecam
build-all: build-bodypix build-fakecam
build-all-gpu: build-bodypixgpu build-fakecam
run-bodypix:
	# start the bodypix app
	docker run -d \
	--name=bodypix \
	--network=fakecam \
	-p 9000:9000 \
	--shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 \
	bodypix
run-bodypixgpu:
	# start the bodypix app
	xhost +
	docker run -d \
	--name=bodypix \
	--network=fakecam \
	-p 9000:9000 \
	--volume=/tmp/.X11-unix:/tmp/.X11-unix \
  	--device=/dev/dri:/dev/dri \
  	--env="DISPLAY=$DISPLAY" \
	--shm-size=1g --ulimit memlock=-1 --ulimit stack=67108864 \
	bodypixgpu
run-fakecam:
	bash -c "source fakecam/fakecamvenv/bin/activate && python -u ./fakecam/fake.py <input_video_filepath"
run-fakecam-docker:
	# start the camera, note that we need to pass through video devices,
	# and we want our user ID and group to have permission to them
	# you may need to `sudo groupadd $USER video`
	docker run -d \
	--name=fakecam \
	--network=fakecam \
	-p 8080:8080 \
	-u $USER --device /dev/video2 --device /dev/video3 --device /dev/video20 \
	fakecam
stop:
	docker stop fakecam
	docker stop bodypix
	docker rm fakecam
	docker rm bodypix
uninstall:
	docker network rm fakecam
