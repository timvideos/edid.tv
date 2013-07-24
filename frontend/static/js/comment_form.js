// Comment
$(function($){
	// Update 'parent' field when reply link is clicked
	$('.comment-reply').click(function(e){
		var id = $(this).data('comment-id');
		$('#id_parent').val(id);
	});
});
