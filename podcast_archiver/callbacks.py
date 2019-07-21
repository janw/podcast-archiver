import logging
from itertools import filterfalse
from os import path
from sys import maxsize

logger = logging.getLogger(__name__)


class Preprocessor:
    episode_count = 0

    def __init__(
        self, max_episodes=maxsize, truncate_existent=False, break_truncation=1
    ):
        self.max_episodes = max_episodes
        self.truncate_existent = truncate_existent
        self.break_truncation = break_truncation

    def callback(self, episodes):

        in_count = len(episodes)
        prospective_count = self.episode_count + in_count
        over = prospective_count - self.max_episodes
        under = len(episodes) - over

        if over > 0:
            logger.debug(f"Reached episode limit, truncating by {over} episodes")
            del episodes[under:]

        # On given option, run an update, break at first existing episode
        if self.truncate_existent:
            episodes[:] = filterfalse(self.check_existing, episodes)

        should_break = (in_count - len(episodes)) >= self.break_truncation

        return episodes, should_break

    @staticmethod
    def check_existing(episode):
        if path.isfile(episode.filename):
            return True
