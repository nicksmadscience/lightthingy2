import yaml
import socket
import time


class LightThingy:
    def __init__(self, configpath, physical, universe, ipaddress):
        self.configpath = configpath
        self.channels = [0] * 512
        self.physical = physical
        self.universe = universe
        self.ipaddress = ipaddress
        self.port = 6454
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.config = self.openyaml(configpath)

        self.presets = self.openyaml(self.config["presetsfile"])
        

    def openyaml(self, path):
        with open(path) as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                print(exc)
                return None
            

    def changeChannel(self, channel, value):
        """Change a channel on _channels, accounting for the fact that DMX channels conventionally (and per spec) start at 1, not 0."""
        
        self.channels[channel - 1] = value


    def artnetPacketFromChannels(self):
        """Converts a 512-long byte array to a valid ArtNet packet that can be sent straight to a device."""

        channelString = ''
        for channel in self.channels:
            channelString += str(chr(channel))
        header = "Art-Net" + chr(0)   # 1 - ID
        header += chr(0) + "P"        # 2 - OpCode
        header += chr(0)              # 3 - ProtVerHi
        header += chr(14)             # 4 - ProtVerLo
        header += chr(0)              # 5 - Sequence
        header += chr(self.physical)      # 6 - Physical
        header += chr(self.universe)      # 7 - SubUni
        header += chr(0)              # 8 - Net
        header += chr(2) + chr(0)     # 9 - Length
        
        channels = bytearray()
        channels.extend(map(ord, header + channelString))
        
        return channels
    

    def sendChannels(self):
        """Sends an ArtNet packet to the device of your choice.  Set the IP address to x.x.x.255 to broadcast to all
        devices.  Unicasting can help cut back on network traffic and is recommended."""

        self.socket.sendto(self.artnetPacketFromChannels(), 
                           (self.ipaddress, self.port))
        

    def fadeChannels(self, destinationChannels, duration_seconds):
        """Linear crossfade between two sets of channels.  Will change the variable assigned to _channels.
        This function is blocking."""
        # TODO: i don't think i wanna do it this way

        channels = [0] * 512
        oldChannels = self.channels
        for i in range(0, int(duration_seconds * 30 + 1)):
            progress = i / 30.0 / duration_seconds
            
            for channel in range(0, 512):
                channels[channel] = int((oldChannels[channel] * (1.0 - progress)) + (destinationChannels[channel] * progress))

            self.channels = channels
            time.sleep(1.0 / 30.0)


    def hextorgb(self, hex):
        h = hex.lstrip('#')
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    

    def maxBrightness(self, color):
        red = color[0]
        green = color[1]
        blue = color[2]

        max_ = max(red, green, blue)
        multiplier = 255.0 / float(max_)

        red = int(red * multiplier)
        green = int(green * multiplier)
        blue = int(blue * multiplier)

        return (red, green, blue)
    

    def gammaCorrection(self, originalValue, gamma):
        return int(((float(originalValue) / 255.0) ** (1.0 / float(gamma))) * 255.0)
    

    def changeRGB(self, startChannel, rgb):
        """Allows you to set channels with an RGB tuple instead of individually."""

        self.changeChannel(startChannel, self.gammaCorrection(rgb[0], 0.6))
        self.changeChannel(startChannel + 1, self.gammaCorrection(rgb[1], 0.6))
        self.changeChannel(startChannel + 2, self.gammaCorrection(rgb[2], 0.6))

    
    def changeHex(self, startChannel, hex):
        """Allows you to set channels with a CSS-style hex color (e.g. #ff0000) instead of individually."""
        rgb_tuple = self.maxBrightness(self.hextorgb(hex))

        self.changeChannel(startChannel, self.gammaCorrection(rgb_tuple[0], 0.6))
        self.changeChannel(startChannel + 1, self.gammaCorrection(rgb_tuple[1], 0.6))
        self.changeChannel(startChannel + 2, self.gammaCorrection(rgb_tuple[2], 0.6))



if __name__ == "__main__":
    lt = LightThingy("config.yaml", 1, 1, "10.0.0.20")
    lt.changeChannel(1, 255)
    lt.sendChannels()
    lt.fadeChannels([0] * 512, 0.5)
    lt.changeRGB(17, [255, 0, 0])
    lt.changeHex(17, "#ff0000")