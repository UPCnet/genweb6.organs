/**
 * manageFiles: switches Restringit/Públic per fitxer.
 * No fem preventDefault perquè el checkbox es mogui visualment; després AJAX i en error revertim.
 */
(function ($) {
    'use strict';

    var CONFIRM_MSG_SINGLE = 'Voleu canviar la visibilitat d\'aquest fitxer?';
    var CONFIRM_MSG_BOTH = 'S\'esborrarà el fitxer del switch que desactiveu. Es mantindrà l\'altre fitxer. Voleu continuar?';

    function showToast(message, isError) {
        var $toast = $('#manageFilesToast');
        if (!$toast.length) {
            $toast = $('<div id="manageFilesToast" class="position-fixed bottom-0 end-0 p-3 manage-files-toast"></div>').appendTo('body');
        }
        var cls = isError ? 'alert-danger' : 'alert-success';
        var $alert = $('<div class="alert ' + cls + ' alert-dismissible fade show" role="alert">' + message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>');
        $toast.append($alert);
        setTimeout(function () {
            $alert.fadeOut(function () { $(this).remove(); });
        }, 4000);
    }

    $(document).ready(function () {
        $(document).on('change', '.visibility-switch', function () {
            var $row = $(this).closest('.visibility-row');
            var $input = $row.find('input.visibility-switch');
            var nowChecked = $input.prop('checked');
            var wasChecked = !nowChecked;
            var fileUrl = $row.data('file-url');
            var action = $row.data('action');
            var otherAction = $row.data('other-action');
            var hasBothVal = $row.data('has-both');
            var hasBoth = hasBothVal === true || hasBothVal === 'true' || hasBothVal === 'True' || String(hasBothVal) === '1';
            var otherRowId = $row.data('other-row-id');

            var url;
            var switchingAway = false;
            if (nowChecked) {
                url = fileUrl + '/' + action;
            } else {
                switchingAway = true;
                url = fileUrl + '/' + (otherAction || (action === 'hiddenToVisible' ? 'visibleToHidden' : 'hiddenToVisible'));
            }

            var confirmMsg = hasBoth ? CONFIRM_MSG_BOTH : CONFIRM_MSG_SINGLE;
            if (!window.confirm(confirmMsg)) {
                $input.prop('checked', wasChecked);
                return;
            }

            function unlock() {
                $('input.visibility-switch').prop('disabled', false);
                $('#contentManageFiles .manage-files-loading').remove();
            }

            $('input.visibility-switch').prop('disabled', true);
            var $overlay = $('<div class="manage-files-loading" aria-hidden="true"><span class="spinner-border spinner-border-sm me-2" role="status"></span><span>Canviant visibilitat...</span></div>');
            $('#contentManageFiles').append($overlay);

            $.ajax({
                url: url,
                type: 'GET',
                dataType: 'json',
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            }).done(function (data) {
                if (data && data.success) {
                    showToast(data.message || 'Visibilitat del fitxer modificada correctament.', false);
                        if (otherRowId && otherRowId !== 'None') {
                            var $other = $('#contentManageFiles').find('.visibility-row').filter(function () { return $(this).attr('id') === otherRowId; });
                            if ($other.length) { $other.fadeOut(300, function () { $(this).remove(); }); }
                        }
                    var isNowPublic;
                    if (switchingAway) {
                        var $pill = $row.find('.visibility-switch-pill');
                        var $label = $row.find('.visibility-switch-label');
                        var newAction = otherAction || (action === 'hiddenToVisible' ? 'visibleToHidden' : 'hiddenToVisible');
                        isNowPublic = newAction === 'hiddenToVisible';
                        $row.data('action', newAction);
                        $row.data('other-action', action);
                        $row.data('has-both', false);
                        $row.data('other-row-id', '');
                        $pill.removeClass('visibility-switch-public visibility-switch-restringit').addClass(isNowPublic ? 'visibility-switch-public' : 'visibility-switch-restringit');
                        $label.text(isNowPublic ? 'Públic' : 'Restringit');
                        $input.prop('checked', true);
                    } else {
                        isNowPublic = action === 'hiddenToVisible';
                    }
                    var $li = $row.closest('li');
                    var $icon = $li.find('.titleSpan i');
                    if ($icon.length) {
                        $icon.removeClass('text-success text-danger').addClass(isNowPublic ? 'text-success' : 'text-danger');
                    }
                } else {
                    showToast((data && data.message) || 'Error en canviar la visibilitat.', true);
                    $input.prop('checked', wasChecked);
                }
            }).fail(function (xhr) {
                var msg = 'Error en canviar la visibilitat.';
                try {
                    var r = typeof xhr.responseText === 'string' ? JSON.parse(xhr.responseText) : null;
                    if (r && r.message) { msg = r.message; }
                } catch (err) {}
                showToast(msg, true);
                $input.prop('checked', wasChecked);
            }).always(function () {
                unlock();
            });
        });
    });
})(jQuery);
