/* SPDX-License-Identifier: MIT */
(() => {
  'use strict';

  const videos = Array.from(document.querySelectorAll('video[controls]'));
  videos.forEach((video) => {
    video.addEventListener('play', () => {
      videos.forEach((other) => {
        if (other !== video) other.pause();
      });
    });
  });

})();
