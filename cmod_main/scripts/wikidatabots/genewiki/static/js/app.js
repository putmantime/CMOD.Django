$('.ajax-post').on('submit', function(evt) {
  evt.preventDefault();

  var l = Ladda.create( $(this).find('.btn')[0] );
  l.start();

  $.ajax({
      type: 'POST',
      url: $(this).attr('action'),
      data: $(this).serialize(),
      success: function() {
        l.stop();
        //location.reload();
      },
      error: function() {
        l.stop();
      }
    });
});

Ladda.bind('#template .ladda-button')
Ladda.bind('#stub .ladda-button');
