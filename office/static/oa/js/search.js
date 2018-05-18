$( "#office-search" ).submit(function( event ) {
    // Stop form from submitting normally
    event.preventDefault();
    var $result = $( "#seearch-result" );
    $result.html('');
    // Send the data using post
    var posting = $.post( "", $(this).serialize() );

    // Put the results in a div
    posting.done(function( data ) {
        $result.html( data );
    });
});
