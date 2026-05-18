sudo docker run --rm -it \
  --platform linux/amd64 \
  --hostname my-lab-pc \
  --mac-address 02:42:ac:11:00:02 \
  --shm-size=8g \
  -p 6901:6901 \
  -e VNC_PW=password \
  ubuntu:v1



用户名: kasm_user
密码 : password

  