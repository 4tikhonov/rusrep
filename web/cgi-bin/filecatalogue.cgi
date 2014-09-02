#!/usr/bin/perl

use vars qw/$libpath/;
use FindBin qw($Bin);
BEGIN { $libpath="$Bin" };
use lib "$libpath";
use lib "$libpath/../libs";

use utf8;
use Encode;
use DB_File;
use DBI;
use ClioInfra;
use ClioTemplates;
$| = 1;

$countrylink = "datasets/countries";
$indicatorlink ="indicator.html";

$htmltemplate = "$Bin/../templates/countries.tpl";

my %dbconfig = loadconfig("$Bin/../config/russianrep.config");
$site = $dbconfig{root};
$introtext = $dbconfig{intro};
$data2excel = $dbconfig{data2excel};
$scriptdir = $dbconfig{scriptdir};
$workpath = $dbconfig{workpath};
$checkicon = $dbconfig{checkicon};
my ($dbname, $dbhost, $dblogin, $dbpassword) = ($dbconfig{dbname}, $dbconfig{dbhost}, $dbconfig{dblogin}, $dbconfig{dbpassword});
my $dbh = DBI->connect("dbi:Pg:dbname=$dbname;host=$dbhost",$dblogin,$dbpassword,{AutoCommit=>1,RaiseError=>1,PrintError=>0});

my ($dbname, $dbhost, $dblogin, $dbpassword) = ($dbconfig{webdbname}, $dbconfig{dbhost}, $dbconfig{dblogin}, $dbconfig{dbpassword});
my $dbh_web = DBI->connect("dbi:Pg:dbname=$dbname;host=$dbhost",$dblogin,$dbpassword,{AutoCommit=>1,RaiseError=>1,PrintError=>0});
my @time = (localtime)[0..5];
my $create_date = sprintf("%04d-%02d-%02d %02d:%02d", $time[5]+1900, $time[4]+1, $time[3], $time[2], $time[1]);
my $path_date = sprintf("%04d%02d%02d.%02d%02d", $time[5]+1900, $time[4]+1, $time[3], $time[2], $time[1]); 
my $edit_date = $create_date;

$path = $workpath;
$path.="$path_date";

use Getopt::Long;

my $result = GetOptions(
    \%options,
    'csvfile=s' => \$csvfile,
    'all', 'help',
    'topic=s' => \$topic,
    'indicator=s' => \$indicator,
    'year=s' => \$year,
    'country=s' => \$country,
    'command=s' => \$command,
    'uri=s' => \$uri,
    'download=s' => \$download,
    'debug=s' => \$debug
);

$DEBUG = $ARGV[0];
#print "Content-type: text/html\n\n";

$topicID = 1;
$histclass_root = 0;
$HTML = 1;
my $DEBUG = 0;

#$filter_datatype = '7.01';
$uri=~s/\%3D/\=/g;
$uri=~s/\%26/\&/g;
$uri=~s/\=on//g;
$uri=~s/\\\&/\&/g;
print "$uri\n" if ($DEBUG);
#if ($uri=~/^.+\/\S+?\?(\S+)$/)
if ($uri=~/^.+?\?(.+)$/)
{
   $uricom = $1;
}
my @commands = split(/\&/, $uricom);
$DEBUG = 0;
foreach $command (@commands)
{
   #$command = $1;
   #$command=~s/\/\&/ /g;
   #  topic=10&d=7.01
   print "CMD $command <br>\n" if ($DEBUG);
   if ($command=~/topicroot(\d+)/)
   {
	$topicRoots.= "$1, ";
	$data{$command}++;
   }

   if ($command=~/(\S+)\=(\S+)/)
   {
	my $item = $command;
	my ($name, $value) = ($1, $2);
	print "$name => $value <br>\n" if ($DEBUG);
	if ($item=~/(\d+)\.(\d+)/)
	{
#	   $topicIDs.= "$1, ";
#	   $datatypes.= "$2 ";
	}
	if ($name=~/d/)
	{
	   $datatypes.= "'$value', ";
	}
	if ($name=~/topic(\d+)/)
	{
	   $topicIDs = "$1, ";
	}
	$data{$item} = $item;
   }
}
if (keys %data)
{
   mkdir $path unless (-e $path);
}

print "$command >> *$topicIDs*<br>" if ($DEBUG);
$topicIDs=~s/\,\s+$//g;
$topicRoots=~s/\,\s+$//g;
$datatypes=~s/\,\s+$//g;
print "DATATYPES: $datatypes\n" if ($DEBUG);
$html = readtopics($topicIDs,'',$filter_datatype);

sub readtopics
{
    my ($topicIDs, $histclass_root, $filter_datatype) = @_;
    my ($html, $datalinks);

    $histclass_root = '0' unless ($histclass_root);
    $sqlquery = "select topic_id, datatype, topic_name, description, topic_root from datasets.topics where 1=1";
    $sqlquery.=" and topic_id in ($topicIDs)" if ($topicIDs);
    $sqlquery.=" and topic_root in ($topicRoots)" if ($topicRoots);
    $sqlquery.=" and datatype in ($datatypes)" if ($datatypes=~/\d+/);
#    $sqlquery.=" order by topic_name asc";
    print "$sqlquery\n" if ($DEBUG);

    @years = (1795, 1858, 1897, 1959, 2002);
    $thisyear = "1897";
    $active{$thisyear}++;
    if ($sqlquery)
    {
        my $sth = $dbh->prepare("$sqlquery");
        $sth->execute();

	while (my ($topic_id, $datatype, $topic_name, $description, $topic_root) = $sth->fetchrow_array())
        {
	    my $topicdata;
	    $filename = "ERRHS_".$datatype."_data_".$thisyear.".xls";
	    if (keys %data)
	    {
	        $datalinks.= "<a href=\"/tmp/dataset.$datatype.xls\">Excel for $topic_name</a> $datatype $path<br>";
	        $datafile = `$data2excel -y $thisyear -d $datatype -f $filename -p $path -D`;
		push(@datafiles, $datafile);
	    }
	    #print "$generator DEBUG <BR>";

	    unless ($topic_root)
	    {
		if ($HTML)
		{
		    my $topic_nameurl = "<a href=\"#\">$topic_name</a>";
                    my $status;
                    $status = "checked" if (keys %data);
		    $htmltopic.="\n<tr><td class=\"indicator\" width=\"20%\"><font color=\"#ffffff\">&nbsp;<input type=\"checkbox\" name=\"topicroot$datatype\" $checked>&nbsp;$topic_nameurl&nbsp;</font></td><td bgcolor=#efefef width=50%></td>\n";
		}
		else
		{
		   print "$topic_name\n" if ($DEBUG);
		}
	    }
	    else
	    {
#	        print "	$datatype $topic_name\n";
		my $topic_nameurl = "<a href=\"#\">$topic_name</a>";
		$topic_nameurl = "$topic_name";
		my $status;
		$status = "checked" if (keys %data);
		$htmltopic.="\n<td></td><td width=50%>&nbsp;<input type=\"checkbox\" name=\"d=$datatype\" $status>&nbsp;$datatype $topic_nameurl</td>";
	        #$topicdata = readclasses($topic_root, $datatype) if (($datatype eq $filter_datatype) || !$filter_datatype);
		#$topicdata = "&nbsp;No data\n" unless ($topicdata);
		#$htmltopic.="$topicdata</td>"; # if ($topicdate);
	    }

	    foreach $year (@years)
	    {
		if ($active{$year})
		{
		     $url = "?topic=$topic_id&d=$datatype";
		     $htmltopic.="<td width=\"5%\" align=\"center\"><img width=20 height=20 src=\"/$checkicon\"></td>";
		}
		else
		{
		    $htmltopic.= "<td width=\"5%\" align=\"center\"><img width=20 height=20 src=\"/absent.jpg\"></td>";
		}
	    }
	    $htmltopic.="</tr>";

#	    $topicdata = "top";
            #$htmltopic.="<td>$topicdata</td></tr>\n"; # if ($topicdata);
	}
    }

    $ziparc = "$path_date.zip";
    my $zipcommand = "cd $path;/usr/bin/zip -9 -y -r -q $ziparc *;/bin/mv $ziparc ../;/bin/rm -rf $path";
    $runzip = `$zipcommand` if (-e $path);
    $datalinks = "Download all data and documentation as one <a href=\"/tmp/$ziparc\">zipfile $topic_name</a><br>";

    my $downloadtext = "<input type=\"submit\" class=\"download\" value=\"Download Selected Datasets\">";
    $downloadtext = '' if (keys %data);
    $downloadlink = "
    <table width=100% border=0>
    <thead>
    <tr><td>$introtext</td></tr>
    <tr><td>Note: You can click on any historical class if you want to download available data for specific regions of Russia or years.<br>
    By default all data for all regions for selected historical classes will be selected.
    </td><td align=right>
    &nbsp;$downloadtext
    </td></tr>
    </thead>
    </table>
    ";

    $html.="<table border=1 class=\"rrtable\">
	<thead>
	<tr align=center><td>&nbsp;</td><td>Datatype</td><td>1795</td><td>1858</td><td>1897</td><td>1959</td><td>2002</td></tr>
	</thead>
	<tbody>
	$htmltopic
	</tbody>
	</table>";
    $html="
    <form name=\"submit\" action=\"/datasets/indicators\" method=\"get\">
    $downloadlink
$html
    $datalinks
    $downloadlink
    </form>
    ";
    print "$html\n";
    exit(0);
}

sub readclasses
{
    my ($topicID, $datatype, $histclass_root) = @_;
    my (%classes, $htmlclass);

    $histclass_root = '0' unless ($histclass_root);
    $sqlquery = "select * from datasets.histclasses where datatype='$datatype'"; # and histclass_root='$histclass_root' limit 100;";
    print "$sqlquery\n" if ($DEBUG);

    if ($sqlquery)
    {
        my $sth = $dbh->prepare("$sqlquery");
        $sth->execute();

        # histclass_id | topic | datatype |                                                           histclass1                                                           | histclass2 | histclass3 | histclass_root | level |   index
        while (my ($histclass_id, $topic, $datatype, $histclass1, $histclass2, $histclass3, $histclass_root, $level, $index) = $sth->fetchrow_array())
        {
	    #print "D $histclass1\n";
	    $classes{$histclass1}{$histclass2}{$histclass3} = "$histclass_id%%$topic%%$datatype%%$histclass_root%%$level%%$index";
        };
    };

my $htmllevel1;
foreach $histclass1 (sort keys %classes)
{
    my %class2 = %{$classes{$histclass1}};
    print "\t\t$histclass1\n" if ($histclass1 ne '0' && $DEBUG);
    $histclass1url = "<a href=\"#\">$histclass1</a>";
    $htmllevel1.="\t\t<tr><td width=200 style=\"vertical-align: top;\">&nbsp;<input type=\"checkbox\">&nbsp;$histclass1url</td>\n" if ($histclass1 ne '0' && $HTML);
 
    my $htmllevel2;
    foreach $class2 (sort keys %class2)
    {
	my %class3 = %{$class2{$class2}};
	print "\t\t\t$class2\n" if ($class2 ne '0' && $DEBUG);
	my $class2url = "<a href=\"#\">$class2</a>";
	$htmllevel2.="\t\t\t<tr><td width=200>&nbsp;<input type=\"checkbox\">&nbsp;$class2url\t\t\t</td>\n" if ($class2 ne '0' && $HTML);

	my $htmllevel3;
	foreach $class3 (sort keys %class3)
	{
	    print "\t\t\t\t$class3\n" if ($class3 ne '0' && $DEBUG); 
	    my $class3url = "<a href=\"#\">$class3</a>";
	    $htmllevel3.="\t\t\t\t<tr><td style=\"vertical-align: top;\"><input type=\"checkbox\"> $class3url\t\t\t\t</td></tr>\n" if ($class3 ne '0' && $HTML);
	}
	$htmllevel2.="\n\t\t\t\t<td width=200 style=\"vertical-align: top;\"><table border=0 bgcolor=#efefef>\n&nbsp;$htmllevel3\t\t\t\t</table></td>\n" if ($htmllevel3);
	$htmllevel2.="</tr>" if ($class2 ne '0' && $HTML);
    }
    $htmllevel2 = "\n\t\t\t<td width=600 style=\"vertical-align: top;\"><table border=0 bgcolor=#efefef>\n&nbsp;$htmllevel2\t\t\t</table></td>\n" if ($htmllevel2);
    $htmllevel1.="$htmllevel2</tr>";
}

$htmllevel1 = "\n\t\t<table border=1>\n$htmllevel1\t\t</table>\n";

   return $htmllevel1;
}

foreach $item (sort {$dataindex{$a} <=> $dataindex{$b}} keys %dataindex)
{
    $first = $datachr{$item};
    
    if (!$known{$first})
    {
	print "<p><a href=\"#index\">index</a></p>" if ($published); 
        print "<p><b><a name=\"$data{$item}\">$first</a></b></p>";
	$published++;
    };
    
    my $tab = "&nbsp;&nbsp;&nbsp;";
    print "\t<input type=\"checkbox\">$tab$item<br>\n";
    $known{$first}++;
}
