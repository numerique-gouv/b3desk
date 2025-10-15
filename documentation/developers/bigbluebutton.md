# BigBlueButton container

If you don't have access to a BBB instance to run B3Desk and test it, you can run a BBB container.

Here is the steps you need to follow to have a local BBB container that is correctly configured.

## Installation steps

There is an [official script](https://github.com/bigbluebutton/docker-dev) to build BBB Docker image.
It has been copied in `bigbluebutton/create_bbb.sh`.

```bash
./bigbluebutton/create_bbb.sh --image=imdt/bigbluebutton:3.0.x-develop --update bbb30
```
The image is quite large (~8Go) so you will have to be patient.

- The script should prompt the url and the secret of the BBB service.
```
    URL: https://bbb30.test/bigbluebutton/
    Secret: unknownBbbSecretKey

    Link to the API-Mate:
    https://bbb30.test/api-mate/#server=https://bbb30.test/bigbluebutton/&sharedSecret=bbbSecretKey

```
This command also shows you how to access the BBB API-Mate.

- Copy the BBB url (BIGBLUEBUTTON_ENDPOINT) and add `api` in the end and secret key (BIGBLUEBUTTON_SECRET) in your web.env file
- Launch B3Desk containers
- You know have a b3desk_default with all services running in it and a standalone BBB service
- You need to connect them together with:

```
docker network connect b3desk_default bbb30
```

You can check if those services are effectively connected with a curl from bbb30 to a B3Desk service for instance

## Launch existing container

If you have already installed BBB and the container still exists, there is no need to install it again (the script `create_bbb.sh` removes any instance and recreates an updated version).

You just need to connect the services :
```
docker network connect b3desk_default bbb30
```

And run the BBB container :
```
docker start bbb30
```

You can check if it is effectively running with :
```
docker ps -a
```

## Configure MP4 recording

To configure BBB to process recordings as MP4 video, as in production, you need some [manual intervention](https://docs.bigbluebutton.org/administration/customize/#install-additional-recording-processing-formats). This is an issue that is [not yet fixed](https://github.com/bigbluebutton/bigbluebutton/issues/12241).

- Open a session in the container:

```
ssh bbb30
```

- Install the bbb-playback-video packaging:

```
sudo apt-get install bbb-playback-video
```

- Edit the `/usr/local/bigbluebutton/core/scripts/bigbluebutton.yml` file:

```
sudo vim /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml
```

- Add video processing and publishing in the file:

```
steps:
  archive: "sanity"
  sanity: "captions"
  captions:
    - "process:presentation"
    - "process:video"
  "process:presentation": "publish:presentation"
  "process:video": "publish:video"
```

- Restart the recording processing queue

```
sudo systemctl restart bbb-rap-resque-worker.service
```
