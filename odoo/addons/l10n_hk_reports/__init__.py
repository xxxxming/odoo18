from . import models


def _l10n_hk_reports_post_init(env):
    for company in env['res.company'].search([('chart_template', '=', 'hk')]):
        ChartTemplate = env['account.chart.template'].with_company(company)
        ChartTemplate._load_data({
            'res.company': ChartTemplate._get_hk_reports_res_company(company.chart_template),
        })
