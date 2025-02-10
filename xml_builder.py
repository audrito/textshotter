from jinja2 import Environment, FileSystemLoader, BaseLoader
import uuid
import os

LOCAL_DIRECTORY = os.getcwd()


def calculate_image_and_audio_timings(image_durations_sec, audio_duration_sec, audio_path, fps):
    """
    Calculates start and end times in frames for images and audio.

    Args:
        image_durations_sec: A dictionary where keys are image paths and 
                             values are their durations in seconds.
        audio_path: The path to the audio file.
        audio_duration_sec: The duration of the audio clip in seconds.
        fps: Frames per second (default is 60).

    Returns:
        A tuple containing two lists of dictionaries:
            - image_timings: Each dictionary contains 'image_path', 'start', 
                             'end', and 'name'.
            - audio_timings: Each dictionary contains 'audio_path', 'start', 
                             'end', and 'name'.
    """

    image_timings = []
    audio_timings = []
    current_frame = 0

    for image_path, duration_sec in image_durations_sec.items():
        image_start_frame = current_frame
        image_end_frame = current_frame + int(round(duration_sec * fps))  # Convert to frames

        image_name = os.path.basename(image_path)

        image_timings.append({
            'image_path': image_path,
            'start': image_start_frame,
            'end': image_end_frame,
            'name': image_name
        })

        audio_start_frame = current_frame
        audio_end_frame = current_frame + int(round(audio_duration_sec * fps))  # Use audio_duration_sec

        audio_name = os.path.basename(audio_path)

        audio_timings.append({
            'audio_path': audio_path,
            'start': audio_start_frame,
            'end': audio_end_frame,
            'name': audio_name
        })

        current_frame = image_end_frame

    return image_timings, audio_timings


# Define the Jinja2 template as a string
TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
    <sequence id="sequence-1" TL.SQAudioVisibleBase="0" TL.SQVideoVisibleBase="0" TL.SQVisibleBaseTime="0" TL.SQAVDividerPosition="0.5" TL.SQHideShyTracks="0" TL.SQHeaderWidth="236" MZ.Sequence.PreviewFrameSizeHeight="1920" MZ.Sequence.PreviewFrameSizeWidth="1080">
        <uuid>15d47889-7681-4668-8fd5-e79bc6ec8461</uuid>
        <duration>{{ total_duration }}</duration>
        <rate>
            <timebase>60</timebase>
            <ntsc>FALSE</ntsc>
        </rate>
        <name>Sequence 01</name>
        <media>
            <video>
                <format>
                    <samplecharacteristics>
                        <rate>
                            <timebase>60</timebase>
                            <ntsc>FALSE</ntsc>
                        </rate>
                        <width>1080</width>
                        <height>1920</height>
                        <anamorphic>FALSE</anamorphic>
                        <pixelaspectratio>square</pixelaspectratio>
                        <fielddominance>none</fielddominance>
                        <colordepth>24</colordepth>
                    </samplecharacteristics>
                </format>
                <track TL.SQTrackShy="0" TL.SQTrackExpandedHeight="41" TL.SQTrackExpanded="0" MZ.TrackTargeted="1">
                    {% for clip in video_clips %}
                    <clipitem id="clipitem-{{ loop.index }}">
                        <masterclipid>masterclip-{{ loop.index }}</masterclipid>
                        <name>{{ clip.name }}</name>
                        <enabled>TRUE</enabled>
                        <duration>1294705</duration>
                        <rate>
                            <timebase>30</timebase>
                            <ntsc>TRUE</ntsc>
                        </rate>
                        <start>{{ clip.start }}</start>
                        <end>{{ clip.end }}</end>
                        <in>0</in>
                        <out>{{ clip.end - clip.start }}</out>
                        <file id="file-{{ loop.index }}">
                            <name>{{ clip.name }}</name>
                            <pathurl>file://localhost/{{ clip.image_path }}</pathurl>
                            <rate>
                                <timebase>30</timebase>
                                <ntsc>TRUE</ntsc>
                            </rate>
                            <media>
                                <video>
                                    <samplecharacteristics>
                                        <rate>
                                            <timebase>30</timebase>
                                            <ntsc>TRUE</ntsc>
                                        </rate>
                                        <width>1080</width>
                                        <height>1920</height>
                                        <anamorphic>FALSE</anamorphic>
                                        <pixelaspectratio>square</pixelaspectratio>
                                        <fielddominance>none</fielddominance>
                                    </samplecharacteristics>
                                </video>
                            </media>
                        </file>
                        <filter>
<effect>
								<name>Basic Motion</name>
								<effectid>basic</effectid>
								<effectcategory>motion</effectcategory>
								<effecttype>motion</effecttype>
								<mediatype>video</mediatype>
								<pproBypass>false</pproBypass>
								<parameter authoringApp="PremierePro">
									<parameterid>scale</parameterid>
									<name>Scale</name>
									<valuemin>0</valuemin>
									<valuemax>1000</valuemax>
									<value>61</value>
								</parameter>
								<parameter authoringApp="PremierePro">
									<parameterid>rotation</parameterid>
									<name>Rotation</name>
									<valuemin>-8640</valuemin>
									<valuemax>8640</valuemax>
									<value>0</value>
								</parameter>
								<parameter authoringApp="PremierePro">
									<parameterid>center</parameterid>
									<name>Center</name>
									<value>
										<horiz>0</horiz>
										<vert>0</vert>
									</value>
								</parameter>
								<parameter authoringApp="PremierePro">
									<parameterid>centerOffset</parameterid>
									<name>Anchor Point</name>
									<value>
										<horiz>0</horiz>
										<vert>0</vert>
									</value>
								</parameter>
								<parameter authoringApp="PremierePro">
									<parameterid>antiflicker</parameterid>
									<name>Anti-flicker Filter</name>
									<valuemin>0.0</valuemin>
									<valuemax>1.0</valuemax>
									<value>0</value>
								</parameter>
							</effect>
                        </filter>
                    </clipitem>
                    {% endfor %}
                    <enabled>TRUE</enabled>
                    <locked>FALSE</locked>
                </track>
            </video>
            <audio>
                <numOutputChannels>2</numOutputChannels>
                <format>
                    <samplecharacteristics>
                        <depth>16</depth>
                        <samplerate>48000</samplerate>
                    </samplecharacteristics>
                </format>
                <outputs>
                    <group>
                        <index>1</index>
                        <numchannels>1</numchannels>
                        <downmix>0</downmix>
                        <channel>
                            <index>1</index>
                        </channel>
                    </group>
                    <group>
                        <index>2</index>
                        <numchannels>1</numchannels>
                        <downmix>0</downmix>
                        <channel>
                            <index>2</index>
                        </channel>
                    </group>
                </outputs>
                <track TL.SQTrackAudioKeyframeStyle="0" TL.SQTrackShy="0" TL.SQTrackExpandedHeight="41" TL.SQTrackExpanded="0" MZ.TrackTargeted="1" PannerCurrentValue="0.5" PannerIsInverted="true" PannerStartKeyframe="-91445760000000000,0.5,0,0,0,0,0,0" PannerName="Balance" currentExplodedTrackIndex="0" totalExplodedTrackCount="2" premiereTrackType="Stereo">
                    {% for clip in audio_clips %}
                    <clipitem id="clipitem-audio-{{ loop.index * 2 - 1 }}" premiereChannelType="stereo">
                        <masterclipid>masterclip-audio-{{ loop.index }}</masterclipid>
                        <name>{{ clip.name }}</name>
                        <enabled>TRUE</enabled>
                        <duration>25</duration>
                        <rate>
                            <timebase>60</timebase>
                            <ntsc>FALSE</ntsc>
                        </rate>
                        <start>{{ clip.start }}</start>
                        <end>{{ clip.end }}</end>
                        <in>8</in>
                        <out>24</out>
                        <file id="file-audio-{{ loop.index }}">
                            <name>{{ clip.name }}</name>
                            <pathurl>file://localhost/{{ clip.audio_path }}</pathurl>
                            <rate>
                                <timebase>30</timebase>
                                <ntsc>TRUE</ntsc>
                            </rate>
                            <duration>25</duration>
                            <media>
                                <audio>
                                    <samplecharacteristics>
                                        <depth>16</depth>
                                        <samplerate>44100</samplerate>
                                    </samplecharacteristics>
                                    <channelcount>2</channelcount>
                                </audio>
                            </media>
                        </file>
                        <sourcetrack>
                            <mediatype>audio</mediatype>
                            <trackindex>1</trackindex>
                        </sourcetrack>
                        <link>
                            <linkclipref>clipitem-audio-{{ loop.index * 2 - 1 }}</linkclipref>
                            <mediatype>audio</mediatype>
                            <trackindex>1</trackindex>
                            <clipindex>{{ loop.index }}</clipindex>
                            <groupindex>1</groupindex>
                        </link>
                        <link>
                            <linkclipref>clipitem-audio-{{ loop.index * 2 }}</linkclipref>
                            <mediatype>audio</mediatype>
                            <trackindex>2</trackindex>
                            <clipindex>{{ loop.index }}</clipindex>
                            <groupindex>1</groupindex>
                        </link>
                    </clipitem>
                    {% endfor %}
                    <enabled>TRUE</enabled>
                    <locked>FALSE</locked>
                    <outputchannelindex>1</outputchannelindex>
                </track>
                <track TL.SQTrackAudioKeyframeStyle="0" TL.SQTrackShy="0" TL.SQTrackExpandedHeight="41" TL.SQTrackExpanded="0" MZ.TrackTargeted="1" PannerCurrentValue="0.5" PannerIsInverted="true" PannerStartKeyframe="-91445760000000000,0.5,0,0,0,0,0,0" PannerName="Balance" currentExplodedTrackIndex="1" totalExplodedTrackCount="2" premiereTrackType="Stereo">
                    {% for clip in audio_clips %}
                    <clipitem id="clipitem-audio-{{ loop.index * 2 }}" premiereChannelType="stereo">
                        <masterclipid>masterclip-audio-{{ loop.index }}</masterclipid>
                        <name>{{ clip.name }}</name>
                        <enabled>TRUE</enabled>
                        <duration>25</duration>
                        <rate>
                            <timebase>60</timebase>
                            <ntsc>FALSE</ntsc>
                        </rate>
                        <start>{{ clip.start }}</start>
                        <end>{{ clip.end }}</end>
                        <in>0</in>
                        <out>{{ (clip.end - clip.start) * 60 }}</out>
                        <file id="file-audio-{{ loop.index }}"/>
                        <sourcetrack>
                            <mediatype>audio</mediatype>
                            <trackindex>2</trackindex>
                        </sourcetrack>
                        <link>
                            <linkclipref>clipitem-audio-{{ loop.index * 2 - 1 }}</linkclipref>
                            <mediatype>audio</mediatype>
                            <trackindex>1</trackindex>
                            <clipindex>{{ loop.index }}</clipindex>
                            <groupindex>1</groupindex>
                        </link>
                        <link>
                            <linkclipref>clipitem-audio-{{ loop.index * 2 }}</linkclipref>
                            <mediatype>audio</mediatype>
                            <trackindex>2</trackindex>
                            <clipindex>{{ loop.index }}</clipindex>
                            <groupindex>1</groupindex>
                        </link>
                    </clipitem>
                    {% endfor %}
                    <enabled>TRUE</enabled>
                    <locked>FALSE</locked>
                    <outputchannelindex>2</outputchannelindex>
                </track>
            </audio>
        </media>
        <timecode>
            <rate>
                <timebase>60</timebase>
                <ntsc>FALSE</ntsc>
            </rate>
            <string>00:00:00:00</string>
            <frame>0</frame>
            <displayformat>NDF</displayformat>
        </timecode>
    </sequence>
</xmeml>'''

def generate_fcpxml(video_clips, audio_clips):
    """
    Generate Final Cut Pro XML from video and audio clip data.
    
    Args:
        video_clips (list): List of dictionaries containing video clip information
        audio_clips (list): List of dictionaries containing audio clip information
    
    Returns:
        str: Generated XML string
    """
    # Calculate total duration based on the last ending time
    total_duration = max(
        max(clip['end'] for clip in video_clips),
        max(clip['end'] for clip in audio_clips)
    )
    
    # Create Jinja2 environment and template
    env = Environment(loader=BaseLoader())
    template = env.from_string(TEMPLATE)
    
    # Render template with clip data
    xml_content = template.render(
        video_clips=video_clips,
        audio_clips=audio_clips,
        total_duration=total_duration
    )
    
    return xml_content

def create_xml(image_durations_sec, audio_duration_sec=0.3, audio_path=rf'{LOCAL_DIRECTORY}\discord-notification.mp3', fps=60):
    try:

        image_clips, audio_clips = calculate_image_and_audio_timings(image_durations_sec, audio_duration_sec=audio_duration_sec, audio_path=audio_path, fps=60)

        xml_content = generate_fcpxml(image_clips, audio_clips)
    
        with open('/chat/output.xml', 'w', encoding='utf-8') as f:
            f.write(xml_content)
        print("✅ Successfully generated XML file, ready to import in Premiere Pro")
    except:
        print('❌ An error occured while generating XML, could not finish.')
