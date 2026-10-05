# %%
from matplotlib.lines import Line2D
import matplotlib.ticker
IMP_LABEL = 'Doldurulmuş (interpolyasiya)'
def plot_filled(ax, years, values, imputed, color, label=None, marker='o', lw=1.5):
    '''Observed points: filled markers, solid segments. Filled (imputed) points: hollow markers; any segment touching a
    filled point is dashed.'''
    y = np.asarray(years); v = np.asarray(values, float); m = np.asarray(imputed, bool); o = np.argsort(y); y, v, m = y[o], v[o], m[o]
    for i in range(len(y) - 1):
        ax.plot(y[i:i + 2], v[i:i + 2], color=color, lw=lw, ls='--' if (m[i] or m[i + 1]) else '-')
    ax.plot(y[~m], v[~m], marker, color=color, ms=4, ls='none', label=label)
    if m.any(): ax.plot(y[m], v[m], marker, color=color, ms=5, ls='none', mfc='white', mew=1.3)
    ax.xaxis.set_major_locator(matplotlib.ticker.MaxNLocator(integer=True))
def imp_legend(ax, **kw):
    h, l = ax.get_legend_handles_labels()
    ax.legend(h + [Line2D([], [], color='grey', ls='--', marker='o', mfc='white', label=IMP_LABEL)], l + [IMP_LABEL], **kw)
def fill_series(F, unit, var):
    d = F[(F.unit == unit) & (F['var'] == var)].sort_values('year'); return d.year.values, d.value.values, d.imputed.values

fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for i, g in enumerate(GRP):
    plot_filled(ax[0], *fill_series(FA, g, 'entry'), PAL[i % len(PAL)], GROUPS[g][0])
    plot_filled(ax[1], *fill_series(FA, g, 'exit'), PAL[i % len(PAL)])
ax[0].set_title('Entry rate by activity, % (006)'); ax[1].set_title('Exit rate by activity, %'); imp_legend(ax[0], fontsize=7, ncol=2)
imp_legend(ax[1], fontsize=7)
_p = PCM_G.PCM.unstack(0).loc[2010:]
for i, g in enumerate(_p.columns): ax[2].plot(_p.index, _p[g], color=PAL[i % len(PAL)], label=g)
ax[2].set_title('Price-cost margin proxy by group, % of output'); ax[2].legend(fontsize=7, ncol=3)
plt.tight_layout(); plt.show()

fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
for j, (var, lab) in enumerate([('new', 'new registrations'), ('dereg', 'deregistrations')]):
    plot_filled(ax[0], *fill_series(FA, 'ALL', var), PAL[j], lab)
ax[0].set_title('All activity groups (006), units: 2021 filled'); imp_legend(ax[0], fontsize=7)
for i, g in enumerate(GRP):
    plot_filled(ax[1], *fill_series(FS_, g, 'sme_output_share'), PAL[i % len(PAL)], g)
ax[1].set_title('SME share of output by group, % (012): 2021 filled'); imp_legend(ax[1], fontsize=7, ncol=3)
for i, s in enumerate(['C', 'F', 'G', 'H', 'I', 'J', 'M']):
    plot_filled(ax[2], *fill_series(FSEC, s, 'entry'), PAL[i % len(PAL)], f'{s} {SECT[s][0][:18]}')
ax[2].set_title('Register entry rate by NACE section, % (2_1): 2022-2023 filled'); imp_legend(ax[2], fontsize=7)
plt.tight_layout(); plt.show()
