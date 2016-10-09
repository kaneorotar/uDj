#!/usr/bin/python3
import vlc
import pika
import time
import threading
import json

"""
    Commands:
        request:
            - uri
        stop
        pause

    Replies sent back:
        done
"""
COMMAND_REQUEST = "request"
COMMAND_STOP = "stop"
COMMAND_PAUSE = "pause"


class Player:

    def __init__(self):
        self.instance = vlc.Instance()
        self.player = self.instance.media_player_new()
        self.callback = None

    def _play(self, uri):
        def run():
            media = self.instance.media_new(uri)
            self.player.set_media(media)
            self.player.play()

            print(self.player.get_state())
            while self.player.get_state() == vlc.State.Playing or self.player.get_state() == vlc.State.Opening:
                time.sleep(1)
                continue
            print("Done!")
            self.callback()

        thread = threading.Thread(target=run)
        thread.start()

    def _pause(self):
        self.player.pause()

    def _stop(self):
        self.player.stop()

    def set_callback(self, callback):
        self.callback = callback

    def listen(self, ch, method, properties, body):
        content = json.loads(str(body, "utf-8"))
        command_type = content["command_type"]
        if command_type == COMMAND_REQUEST:
            self._play(content["song"])
        elif command_type == COMMAND_PAUSE:
            self._pause()
        elif command_type == COMMAND_STOP:
            self._stop()
        else:
            raise Exception("You fucked up")


def main():

    def notify():
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        channel = connection.channel()
        channel.queue_declare(queue='song_complete_queue')
        channel.basic_publish(exchange='', routing_key='song_complete_queue', body='done')

    player = Player()
    player.set_callback(notify)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='command_queue')

    channel.basic_consume(player.listen, queue='command_queue', no_ack=True)
    channel.start_consuming()


if __name__ == "__main__":
    main()