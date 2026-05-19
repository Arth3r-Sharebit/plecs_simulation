sudo docker run --rm -it \
  --platform linux/amd64 \
  --hostname my-lab-pc \
  --mac-address 02:42:ac:11:00:02 \
  --shm-size=8g \
  -p 6901:6901 \
  -e VNC_PW=password \
  ubuntu:v1


sudo docker run --rm -it \
  --platform linux/amd64 \
  --hostname my-lab-pc \
  --mac-address 02:42:ac:11:00:02 \
  --shm-size=8g \
  -p 6901:6901 \
  -e VNC_PW=password \
  -e USER_PASSWORD=password \
  -v ~/Downloads/my_images:/home/kasm-user/data kasmweb/core-ubuntu-jammy:x86_64-1.18.0-rolling-daily

用户名: kasm_user
密码 : password

  