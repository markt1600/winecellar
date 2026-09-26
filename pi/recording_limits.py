"""Independent duration, byte and pre-roll bounds for camera recordings."""
MAX_SECONDS=20.0
MAX_RAW_BYTES=3500000
MAX_SEGMENT_BYTES=1000000
MAX_RING_BYTES=1200000
MAX_RING_SEGMENTS=8

def trim_ring(ring,now,pre=5):
 while ring and (ring[0][2]<now-pre-2 or len(ring)>MAX_RING_SEGMENTS or sum(len(s[3]) for s in ring)>MAX_RING_BYTES):ring.popleft()

def can_append(active,segment):
 return active['bytes']+len(segment[3])<=MAX_RAW_BYTES and segment[2]-active['start']<=MAX_SECONDS

def deadline_reached(active,now):
 return now-active['born']>=MAX_SECONDS or active['end']-active['start']>=MAX_SECONDS or active['bytes']>=MAX_RAW_BYTES
