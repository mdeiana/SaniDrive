










AUI.add(
	'portal-available-languages',
	function(A) {
		var available = {};

		var direction = {};

		

			available['it_IT'] = 'italiano (Italia)';
			direction['it_IT'] = 'ltr';

		

			available['en_US'] = 'inglese (Stati Uniti)';
			direction['en_US'] = 'ltr';

		

		Liferay.Language.available = available;
		Liferay.Language.direction = direction;
	},
	'',
	{
		requires: ['liferay-language']
	}
);