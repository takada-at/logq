286M(299542353)のファイルを検索

検索条件

```
(cols[1]>='time:2014-10-01 04:04:00') & (cols[1]<'time:2014-10-01 04:05:00') & (cols[25]=='user_id:3097456')
```

```
## benchmarker:       release 3.0.1 (for python)
## python platform:   linux2 [GCC 4.6.3 20120306 (Red Hat 4.6.3-2)]
## python version:    2.7.3
## python executable: /home/project/statistics/bin/python

##                       user       sys     total      real
logq0               2
   0.6400    0.2000    0.8400    0.8361
logq1               2
   1.9800    0.5500    2.5300    2.5300
notlogq             2
   6.6100    0.1500    6.7600    6.7602
logq0-bz2           2
  12.5500    0.0100   12.5600   12.5632
notlogq-bz2         2
  18.5800    0.0200   18.6000   18.5941

## Ranking               real
logq0                  0.8361 (100.0%) *************************
logq1                  2.5300 ( 33.0%) ********
notlogq                6.7602 ( 12.4%) ***
logq0-bz2             12.5632 (  6.7%) **
notlogq-bz2           18.5941 (  4.5%) *
```

```
## benchmarker:       release 3.0.1 (for python)
## python platform:   linux2 [GCC 4.6.3 20120306 (Red Hat 4.6.3-2)]
## python version:    2.7.3
## python executable: /home/project/statistics/bin/python

##                       user       sys     total      real
logq0               2
   0.7300    0.1600    0.8900    0.8958
logq1               2
   2.1100    0.5700    2.6800    2.6849
notlogq             2
   6.8500    0.1900    7.0400    7.0524
logq0-bz2           2
  12.5500    0.0100   12.5600   12.6044
notlogq-bz2         2
  18.9000    0.0100   18.9100   18.9023

## Ranking               real
logq0                  0.8958 (100.0%) *************************
logq1                  2.6849 ( 33.4%) ********
notlogq                7.0524 ( 12.7%) ***
logq0-bz2             12.6044 (  7.1%) **
notlogq-bz2           18.9023 (  4.7%) *

## Ratio Matrix          real    [01]    [02]    [03]    [04]    [05]
[01] logq0             0.8958  100.0%  299.7%  787.3% 1407.1% 2110.1%
[02] logq1             2.6849   33.4%  100.0%  262.7%  469.4%  704.0%
[03] notlogq           7.0524   12.7%   38.1%  100.0%  178.7%  268.0%
[04] logq0-bz2        12.6044    7.1%   21.3%   56.0%  100.0%  150.0%
[05] notlogq-bz2      18.9023    4.7%   14.2%   37.3%   66.7%  100.0%
```